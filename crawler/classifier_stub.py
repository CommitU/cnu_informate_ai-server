CODES = {"IT":1,"ACADEMIC":2,"SCHOLAR":3,"CLUB":4,"SEMINAR":5,"MARKETING":6,"JOB":7,"ETC":8}
def classify(title:str, content:str):
    t = (title + " " + content).lower()
    if any(k in t for k in ["채용","인턴","recruit","intern"]): return (CODES["JOB"],0.85,"stub-0.1")
    if any(k in t for k in ["장학","scholar"]): return (CODES["SCHOLAR"],0.8,"stub-0.1")
    if any(k in t for k in ["수업","학사","휴학","복학"]): return (CODES["ACADEMIC"],0.75,"stub-0.1")
    return (CODES["ETC"],0.5,"stub-0.1")