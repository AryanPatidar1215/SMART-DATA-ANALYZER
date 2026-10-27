import io
import sqlite3
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent
DB = ROOT / "database" / "analytics.db"
st.set_page_config(page_title="Smart Data Analyzer", page_icon="📊", layout="wide")

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 12% 0%,#182c4d 0%,#0b1220 45%,#090f1d 100%);color:#eaf0ff}
.block-container{max-width:1450px;padding-top:1.5rem}
.hero{border:1px solid #2a4164;border-radius:24px;padding:28px 30px;background:linear-gradient(120deg,#1e3558,#111d31);margin-bottom:18px}
.eyebrow{color:#66e3c4;text-transform:uppercase;letter-spacing:.18em;font-size:12px;font-weight:800}
.hero h1{font-size:36px;margin:8px 0;color:#f5f8ff}.hero p{color:#b8c7e3;margin:0}
.section{color:#a8bad9;font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin:24px 0 10px}
.metric{background:linear-gradient(145deg,#172741,#111b2d);border:1px solid #2b3f5e;border-radius:17px;padding:17px;min-height:105px}
.ml{color:#9eacc8;font-size:12px;text-transform:uppercase;letter-spacing:.08em}
.mv{color:#f3f7ff;font-size:27px;font-weight:750;margin-top:7px}
.mn{color:#66e3c4;font-size:12px;margin-top:3px}
div[data-testid="stDataFrame"],div[data-testid="stPlotlyChart"]{border:1px solid #263754;border-radius:14px;overflow:hidden}
div[data-testid="stFileUploader"]{background:#121d32;border:1px dashed #426187;padding:12px;border-radius:16px}
div.stButton>button,div.stDownloadButton>button{border-radius:10px;border:1px solid #355478}
div.stButton>button[kind="primary"]{background:#66e3c4;color:#07141d;border:none;font-weight:800}
</style>
""", unsafe_allow_html=True)

def read_file(f):
    name=f.name.lower()
    if name.endswith(".csv"):
        try: return pd.read_csv(f)
        except UnicodeDecodeError:
            f.seek(0); return pd.read_csv(f, encoding="latin-1")
    if name.endswith(".xlsx"): return pd.read_excel(f, engine="openpyxl")
    if name.endswith(".xls"): return pd.read_excel(f, engine="xlrd")
    raise ValueError("Upload .csv, .xlsx or .xls")

def unique_columns(cols):
    used=set(); out=[]
    for i,c in enumerate(cols):
        base=str(c).strip() or f"column_{i+1}"; name=base; n=2
        while name in used: name=f"{base}_{n}"; n+=1
        used.add(name); out.append(name)
    return out

def detect_dates(frame):
    frame=frame.copy()
    for col in frame.columns:
        if pd.api.types.is_numeric_dtype(frame[col]): continue
        if any(x in str(col).lower() for x in ["date","time","year","month"]):
            parsed=pd.to_datetime(frame[col],errors="coerce")
            if parsed.notna().sum(): frame[col]=parsed
    return frame

def quality_table(frame):
    out=[]
    for col in frame.columns:
        s=frame[col]
        typ="Date/Time" if pd.api.types.is_datetime64_any_dtype(s) else ("Numeric" if pd.api.types.is_numeric_dtype(s) else "Text / Category")
        out.append({"Column":str(col),"Detected Type":typ,"Non-null":int(s.notna().sum()),"Missing":int(s.isna().sum()),"Missing %":round(s.isna().mean()*100,2),"Unique":int(s.nunique(dropna=True))})
    return pd.DataFrame(out)

def metric(label,value,note):
    st.markdown(f'<div class="metric"><div class="ml">{label}</div><div class="mv">{value}</div><div class="mn">{note}</div></div>',unsafe_allow_html=True)

def xlsx_bytes(sheets):
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as writer:
        for name,frame in sheets.items(): frame.to_excel(writer,sheet_name=name[:31],index=False)
    return buf.getvalue()

st.markdown('<div class="hero"><div class="eyebrow">ANALYTICS WORKSPACE · EXCEL · SQL · TABLEAU</div><h1>Smart Data Analyzer</h1><p>Turn spreadsheets into clear insights. Upload data, explore patterns, run SQL and export a Tableau-ready dataset.</p></div>',unsafe_allow_html=True)
with st.sidebar:
    st.markdown("## ⚙️ Workspace")
    st.markdown("**Workflow**\n\n1. Upload data\n2. Review quality\n3. Explore charts\n4. Run SQL\n5. Export to Tableau")
    st.markdown("---")
    st.caption("CSV · XLSX · XLS")
    st.caption("Do not publish confidential data to Tableau Public.")

uploaded=st.file_uploader("Drop an Excel or CSV file here",type=["csv","xlsx","xls"])
if uploaded is None:
    sample=ROOT/"sample_sales.csv"
    st.info("Upload your own file, or download the sample dataset to try the dashboard.")
    if sample.exists(): st.download_button("⬇ Download sample dataset",sample.read_bytes(),"sample_sales.csv","text/csv")
    st.stop()
try: raw=read_file(uploaded)
except Exception as e: st.error(f"Could not read file: {e}"); st.stop()
if raw.empty: st.error("This file has no data rows."); st.stop()
raw.columns=unique_columns(raw.columns)
df=detect_dates(raw.replace(r"^\s*$",pd.NA,regex=True))
nums=df.select_dtypes(include="number").columns.tolist()
dates=[c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
cats=[c for c in df.columns if c not in nums and c not in dates]
quality=quality_table(df); missing=int(df.isna().sum().sum()); dup=int(df.duplicated().sum())

st.markdown('<div class="section">01 / DATASET SNAPSHOT</div>',unsafe_allow_html=True)
a,b,c,d=st.columns(4)
with a: metric("Total records",f"{len(df):,}","Rows detected")
with b: metric("Data fields",f"{len(df.columns):,}",f"{len(nums)} numeric columns")
with c: metric("Missing cells",f"{missing:,}","Review data quality")
with d: metric("Duplicate rows",f"{dup:,}","Potential duplicates")
with st.expander("🔎 Preview uploaded data",expanded=True): st.dataframe(df.head(100),use_container_width=True,hide_index=True)

st.markdown('<div class="section">02 / DATA QUALITY & CLEANING</div>',unsafe_allow_html=True)
left,right=st.columns([1.4,1])
with left: st.dataframe(quality,use_container_width=True,hide_index=True)
with right:
    st.markdown("#### Clean analysis copy")
    remove=st.toggle("Remove duplicate rows",value=True)
    fill=st.toggle("Fill numeric missing values with median",value=False)
    st.caption("The original file is never overwritten.")
clean=df.copy()
if remove: clean=clean.drop_duplicates()
if fill:
    for col in clean.select_dtypes(include="number").columns:
        if clean[col].isna().any() and pd.notna(clean[col].median()): clean[col]=clean[col].fillna(clean[col].median())

st.markdown('<div class="section">03 / EXPLORE YOUR DATA</div>',unsafe_allow_html=True)
if nums:
    cols=st.columns(min(4,len(nums)))
    for i,col in enumerate(nums[:4]):
        with cols[i]: metric(f"Total {col}",f"{clean[col].sum():,.2f}",f"Average {clean[col].mean():,.2f}" if clean[col].notna().any() else "No values")
else: st.warning("No numeric columns detected. Category analysis and export still work.")
p1,p2=st.columns(2)
with p1:
    if nums:
        chosen=st.selectbox("Distribution · numeric field",nums)
        fig=px.histogram(clean,x=chosen,title=f"Distribution of {chosen}",template="plotly_dark",color_discrete_sequence=["#66e3c4"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig,use_container_width=True)
with p2:
    if cats and nums:
        cat=st.selectbox("Compare by category",cats)
        measure=st.selectbox("Numeric measure",nums,key="measure")
        grouped=clean.groupby(cat,dropna=False)[measure].sum().reset_index()
        grouped[cat]=grouped[cat].fillna("(Missing)").astype(str)
        grouped=grouped.sort_values(measure,ascending=False).head(20)
        fig=px.bar(grouped,x=cat,y=measure,title=f"{measure} by {cat}",template="plotly_dark",color=measure,color_continuous_scale=["#355478","#66e3c4"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig,use_container_width=True)
    elif dates and nums:
        dt=st.selectbox("Date field",dates); measure=st.selectbox("Numeric measure",nums,key="date_measure")
        timeline=clean.dropna(subset=[dt]).copy(); timeline["_period"]=pd.to_datetime(timeline[dt],errors="coerce").dt.to_period("M").astype(str)
        grouped=timeline.groupby("_period")[measure].sum().reset_index()
        fig=px.line(grouped,x="_period",y=measure,markers=True,title=f"{measure} over time",template="plotly_dark",color_discrete_sequence=["#66e3c4"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
if cats:
    cat=st.selectbox("Category breakdown",cats,key="piecat")
    counts=clean[cat].fillna("(Missing)").astype(str).value_counts().head(12).reset_index()
    counts.columns=[cat,"Records"]
    fig=px.pie(counts,names=cat,values="Records",hole=.55,title=f"Records by {cat}",template="plotly_dark",color_discrete_sequence=["#66e3c4","#79a7ff","#f5bd67","#c4a7ff","#ff8d9b"])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",margin=dict(l=10,r=10,t=55,b=10))
    st.plotly_chart(fig,use_container_width=True)

st.markdown('<div class="section">04 / SQL QUERY LAB</div>',unsafe_allow_html=True)
st.caption("The uploaded dataset is available as SQLite table uploaded_data. Only SELECT queries are allowed.")
query=st.text_area("SQL query",value="SELECT * FROM uploaded_data LIMIT 10;",height=100)
if st.button("▶ Run SQL query",type="primary"):
    try:
        if not query.strip().lower().startswith("select"): raise ValueError("Only SELECT queries are allowed.")
        with sqlite3.connect(":memory:") as conn:
            clean.to_sql("uploaded_data",conn,index=False,if_exists="replace")
            result=pd.read_sql_query(query,conn)
        st.session_state["sql_result"]=result
        st.success(f"Query completed · {len(result)} result rows")
    except Exception as e: st.error(f"SQL error: {e}")
if "sql_result" in st.session_state:
    st.dataframe(st.session_state["sql_result"],use_container_width=True,hide_index=True)
    st.download_button("Download SQL results",st.session_state["sql_result"].to_csv(index=False).encode("utf-8"),"sql_results.csv","text/csv")

st.markdown('<div class="section">05 / EXPORT CENTER · TABLEAU READY</div>',unsafe_allow_html=True)
st.write("Download the cleaned dataset and connect it to Tableau for a separate interactive dashboard.")
summary=[]
for col in clean.select_dtypes(include="number").columns:
    s=clean[col]; summary.append({"Column":col,"Count":int(s.count()),"Sum":float(s.sum()),"Average":float(s.mean()) if s.count() else None,"Minimum":float(s.min()) if s.count() else None,"Maximum":float(s.max()) if s.count() else None})
summary=pd.DataFrame(summary,columns=["Column","Count","Sum","Average","Minimum","Maximum"])
csv=clean.to_csv(index=False).encode("utf-8")
report=xlsx_bytes({"Cleaned_Data":clean,"Column_Profile":quality,"Numeric_Summary":summary})
x,y,z=st.columns(3)
with x: st.download_button("⬇ Tableau-ready CSV",csv,"cleaned_tableau_data.csv","text/csv",use_container_width=True)
with y: st.download_button("⬇ Excel analysis report",report,"data_analysis_report.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
with z: st.download_button("⬇ Data quality report",quality.to_csv(index=False).encode("utf-8"),"data_quality_report.csv","text/csv",use_container_width=True)
with st.expander("📈 Tableau dashboard setup"):
    st.markdown("""1. Download **Tableau-ready CSV** above.\n2. Open Tableau Public/Desktop → **Connect → Text File** → select the CSV.\n3. Create a KPI sheet, category bar chart and date trend (if a date field exists).\n4. Select **Dashboard → New Dashboard** and drag sheets into it.\n5. Add filters for region/category/date where available.\n6. Save/publish. Tableau Public workbooks are public, so do not publish confidential data.\n\n**Note:** Website charts update on upload. This mini project exports Tableau-ready data; it does not live-embed or automatically sync each upload to a published Tableau dashboard.""")
if st.button("💾 Save cleaned data to local SQLite database"):
    try:
        DB.parent.mkdir(exist_ok=True)
        with sqlite3.connect(DB) as conn:
            clean.to_sql("uploaded_data",conn,index=False,if_exists="replace")
            quality.to_sql("column_profile",conn,index=False,if_exists="replace")
        st.success("Saved to database/analytics.db (table: uploaded_data).")
    except Exception as e: st.error(f"Could not save to SQLite: {e}")
st.markdown("---")
st.caption("Smart Data Analyzer · Mini project · Automatic column detection is heuristic; verify types and cleaning choices.")
