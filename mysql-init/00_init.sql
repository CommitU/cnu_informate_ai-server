-- 0) 기본 스키마 생성
CREATE DATABASE IF NOT EXISTS cnu_info
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

-- 1) 앱용 계정
CREATE USER IF NOT EXISTS 'cnu_app'@'%' IDENTIFIED BY '비밀번호';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER
ON cnu_info.* TO 'cnu_app'@'%';
FLUSH PRIVILEGES;

-- 2) 세션 기본 설정
USE cnu_info;
SET time_zone = '+09:00';

-- 3) 테이블 (MVP)
CREATE TABLE IF NOT EXISTS category (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  code       VARCHAR(50) UNIQUE NOT NULL,
  name       VARCHAR(100) NOT NULL,
  parent_id  BIGINT NULL,
  CONSTRAINT fk_category_parent FOREIGN KEY (parent_id) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS source (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  name       VARCHAR(100) NOT NULL,
  base_url   VARCHAR(500) NOT NULL,
  type       ENUM('MAIN','COLLEGE','DEPT','CYBER') NOT NULL,
  is_active  TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notice (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  source_id    BIGINT NOT NULL,
  external_id  VARCHAR(100) NULL,
  url          VARCHAR(600) NOT NULL,
  title        VARCHAR(500) NOT NULL,
  content      MEDIUMTEXT NULL,
  posted_at    DATETIME NULL,
  scraped_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deadline_at  DATETIME NULL,
  hash         CHAR(64) NULL,
  CONSTRAINT uq_notice_url UNIQUE (url),
  INDEX idx_notice_source_posted (source_id, posted_at),
  CONSTRAINT fk_notice_source FOREIGN KEY (source_id) REFERENCES source(id)
);

CREATE TABLE IF NOT EXISTS notice_category (
  notice_id     BIGINT NOT NULL,
  category_id   BIGINT NOT NULL,
  confidence    DECIMAL(5,4) NULL,
  model_version VARCHAR(50) NULL,
  PRIMARY KEY (notice_id, category_id),
  INDEX idx_nc_category (category_id),
  CONSTRAINT fk_nc_notice FOREIGN KEY (notice_id) REFERENCES notice(id) ON DELETE CASCADE,
  CONSTRAINT fk_nc_category FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS attachment (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  notice_id  BIGINT NOT NULL,
  file_name  VARCHAR(300) NULL,
  file_url   VARCHAR(600) NOT NULL,
  file_size  BIGINT NULL,
  CONSTRAINT fk_att_notice FOREIGN KEY (notice_id) REFERENCES notice(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_user (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  email         VARCHAR(200) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name          VARCHAR(100) NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_interest_category (
  user_id     BIGINT NOT NULL,
  category_id BIGINT NOT NULL,
  weight      INT NOT NULL DEFAULT 1,
  PRIMARY KEY (user_id, category_id),
  CONSTRAINT fk_uic_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE,
  CONSTRAINT fk_uic_category FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS user_keyword (
  id        BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id   BIGINT NOT NULL,
  keyword   VARCHAR(100) NOT NULL,
  match_type ENUM('CONTAINS','EXACT') NOT NULL DEFAULT 'CONTAINS',
  CONSTRAINT fk_uk_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notification (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id       BIGINT NOT NULL,
  notice_id     BIGINT NOT NULL,
  scheduled_at  DATETIME NOT NULL,
  sent_at       DATETIME NULL,
  status        ENUM('PENDING','SENT','FAILED','CANCELLED') NOT NULL DEFAULT 'PENDING',
  channel       ENUM('WS','WEB_PUSH') NOT NULL DEFAULT 'WS',
  INDEX idx_notif_status_time (status, scheduled_at),
  CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE,
  CONSTRAINT fk_notif_notice FOREIGN KEY (notice_id) REFERENCES notice(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crawl_job (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  source_id   BIGINT NOT NULL,
  started_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  finished_at DATETIME NULL,
  status      ENUM('RUNNING','SUCCESS','FAILED') NOT NULL DEFAULT 'RUNNING',
  error_msg   TEXT NULL,
  CONSTRAINT fk_cj_source FOREIGN KEY (source_id) REFERENCES source(id)
);

-- 4) 시드 데이터
INSERT IGNORE INTO category(code,name) VALUES
 ('IT','IT/개발'),('ACADEMIC','학사/수업'),('SCHOLAR','장학금'),
 ('CLUB','동아리/모임'),('SEMINAR','특강/세미나'),
 ('MARKETING','마케팅/홍보'),('JOB','취업/인턴쉽'),('ETC','기타');

INSERT IGNORE INTO source(name, base_url, type) VALUES
 ('CNU 메인', 'https://plus.cnu.ac.kr/_prog/_board/', 'MAIN');