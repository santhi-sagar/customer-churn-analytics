"""Offline-first portfolio application. Run: streamlit run app.py"""
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from core import CATEGORIES, NUMERIC, load_json, score, read_csv_bytes, synthetic_template

st.set_page_config(page_title='Signal | Customer Churn Intelligence', page_icon='📊', layout='wide')
st.markdown('''<style>
.stApp {background: #0b1220; color: #e9eff8;}
[data-testid="stMetric"] {background: #152238; border:1px solid #273b56; padding:18px; border-radius:14px;}
h1,h2,h3 {letter-spacing:-.025em;} .eyebrow {color:#67e8c3;letter-spacing:.22em;font-size:.8rem;font-weight:700;}
.hero {padding:12px 0 24px;} .hero p {color:#a8bad3;max-width:780px;}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">SIGNAL / TELECOM ANALYTICS</div><h1>Understand churn. Prioritize questions.</h1><p>A transparent portfolio study of IBM’s Telco sample: descriptive segments, reproducible holdout evaluation, and identifier-free risk scoring.</p></div>',unsafe_allow_html=True)
st.info('Educational sample—not a production retention system. Associations are not causes, scores are not guarantees, and no business savings or intervention effects have been measured.')

@st.cache_data
def assets():
    return load_json('dashboard.json'),load_json('evaluation.json'),load_json('model.json')
d,e,m=assets()
with st.sidebar:
    st.header('Study notes')
    st.write('7,043 sample records · 15 model inputs · no demographic inputs')
    st.caption('The source CSV does not contain payment delays, an acquisition date, or measured customer lifetime value.')
    st.metric('Frozen review threshold',f"{m['threshold']:.0%}")
    st.caption('Chosen by validation F1, not business costs. Do not interpret this as an optimal commercial policy.')
    st.markdown('[Source & provenance](https://github.com/IBM/telco-customer-churn-on-icp4d)')
    st.write('No runtime dataset download. Uploaded data is processed in this app session, not intentionally saved. Use only de-identified sample data; hosting infrastructure may retain operational logs.')
    st.download_button('Synthetic input template',synthetic_template().to_csv(index=False),'synthetic_scoring_template.csv','text/csv')

def chart(fig):
    fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#c4d1e5',margin=dict(l=10,r=15,t=40,b=15))
    st.plotly_chart(fig,use_container_width=True)

overview,individual,batch,performance,method=st.tabs(['Portfolio overview','Score one customer','Batch scoring','Model evidence','Definitions & limitations'])
with overview:
    st.subheader('Historical sample overview')
    a,b,c,f=st.columns(4)
    a.metric('Sample customers',f"{d['customers']:,}")
    b.metric('Observed churn rate',f"{d['churn_rate']:.1%}")
    c.metric('Monthly charges · whole sample',f"${d['monthly_charges']:,.0f}")
    f.metric('Monthly charges · churned group',f"${d['churned_monthly_charges']:,.0f}")
    st.caption('Charge values are sample monetary units, displayed as $. Churned-group charges are descriptive historical exposure, not predicted loss, recoverable revenue, ARR, or savings.')
    left,right=st.columns([1.6,1])
    with left:
        dimension=st.selectbox('Compare a segment dimension',['Contract','tenure_band','InternetService','PaymentMethod','TechSupport'],format_func=lambda s:s.replace('_',' ').title())
        seg=pd.DataFrame(d['segments'][dimension])
        fig=px.bar(seg,x='segment',y='churn_rate',text=seg.churn_rate.map(lambda v:f'{v:.1%}'),color='churn_rate',color_continuous_scale=['#27476b','#68e7bd'],labels={'segment':'Segment','churn_rate':'Observed churn rate'})
        fig.update_yaxes(tickformat='.0%');chart(fig)
    with right:
        st.markdown('### From pattern to hypothesis')
        st.write('Compare churn frequency within contract, tenure and service groups. Group sizes matter: a high rate in a small segment is not automatically a large opportunity.')
        st.write('A segment pattern can suggest further investigation. It cannot establish that changing a contract or service will prevent churn.')
        st.caption('Each dimension is a separate whole-sample aggregation; these are not cross-filtered customer-level records.')
    st.dataframe(seg.rename(columns={'monthly_charges':'sum_monthly_charges'}),hide_index=True,use_container_width=True)
    st.download_button('Download displayed aggregate',seg.to_csv(index=False),'churn_segment_aggregate.csv','text/csv')

with individual:
    st.subheader('Single-customer risk explorer')
    st.write('All fields are required. Supported numeric ranges reflect this sample, not a universal telecom population. Defaults are deliberately synthetic, not a source customer.')
    defaults=synthetic_template().iloc[0].to_dict()
    with st.form('single_customer'):
        cols=st.columns(3); values={}
        for i,col in enumerate(NUMERIC):
            if col=='tenure':
                values[col]=cols[i].number_input('Tenure (whole months)',0,72,12,1)
            else:
                values[col]=cols[i].number_input(col+' (sample $)',0.0,120.0 if col=='MonthlyCharges' else 9000.0,float(defaults[col]),.05)
        fields=st.columns(3)
        for i,(name,options) in enumerate(CATEGORIES.items()):
            values[name]=fields[i%3].selectbox(name,options)
        submitted=st.form_submit_button('Calculate sample risk',type='primary')
    if submitted:
        try:
            result=score(pd.DataFrame([values]),m)
            probability=float(result.churn_probability.iloc[0])
            a,b,c=st.columns(3)
            a.metric('Model churn probability',f'{probability:.1%}')
            b.metric('Review flag','Above threshold' if result.review_flag.iloc[0] else 'Below threshold')
            c.metric('Weighted monthly exposure proxy',f"${result.monthly_charge_exposure_proxy.iloc[0]:,.2f}")
            st.caption(f"Threshold {m['threshold']:.0%}. Historical value / CLV proxy: ${result.historical_value_proxy.iloc[0]:,.2f}. Neither proxy measures lifetime profit or preventable loss.")
            st.download_button('Download this score',result.to_csv(index=False),'single_sample_score.csv','text/csv')
        except ValueError as exc:
            st.error(str(exc))

with batch:
    st.subheader('Validated batch scoring')
    st.write('Upload a UTF-8 CSV containing exactly the 15 template columns. No IDs, demographic fields, target label, or other columns. Up to 10,000 rows / 5 MB. Scored output preserves input order via a 1-based row number and does not echo inputs.')
    st.caption('The template is synthetic. Remove identifying information before uploading. This demonstration has no persistent upload storage.')
    upload=st.file_uploader('Choose de-identified scoring CSV',type=['csv'])
    if upload is not None:
        try:
            frame=read_csv_bytes(upload.getvalue()); result=score(frame,m)
            a,b,c=st.columns(3)
            a.metric('Scored rows',f'{len(result):,}')
            b.metric('Review flags',f'{int(result.review_flag.sum()):,}')
            c.metric('Weighted monthly exposure proxy',f'${result.monthly_charge_exposure_proxy.sum():,.2f}')
            st.dataframe(result.head(100),hide_index=True,use_container_width=True)
            st.caption('Preview: first 100 scores. Download contains all scores. Review flag uses the frozen validation-selected threshold.')
            st.download_button('Download all batch scores',result.to_csv(index=False),'churn_scores.csv','text/csv')
        except (ValueError,TypeError) as exc:
            st.error('Upload rejected: '+str(exc))

with performance:
    st.subheader('Held-out evidence, not training accuracy')
    st.write(f"Train / validation / test: {e['split']['train']:,} / {e['split']['validation']:,} / {e['split']['test']:,}. Stratified 60/20/20 random split, seed 42. Selected: {e['selected_model']}.")
    hm=e['holdout_selected']
    cols=st.columns(4)
    for col,key,label in zip(cols,['roc_auc','average_precision','recall','precision'],['ROC-AUC','Average precision','Recall','Precision']):
        col.metric(label,f'{hm[key]:.3f}')
    st.dataframe(pd.DataFrame([{'model':'Frozen selected model',**hm},{'model':'Prior baseline (threshold 0.5)',**e['holdout_baseline_at_0_5']}]),hide_index=True,use_container_width=True)
    st.caption('Average precision summarizes the precision–recall ranking curve (not trapezoidal PR-AUC). Brier score: lower is better. Baseline predicts training prevalence; its 0.5 classification predicts no churn. No temporal or external validation.')
    l,r=st.columns(2)
    with l:
        fig=go.Figure([go.Scatter(x=e['roc']['fpr'],y=e['roc']['tpr'],name='Selected model'),go.Scatter(x=[0,1],y=[0,1],name='Random',line=dict(dash='dash'))]);fig.update_layout(title='Holdout ROC',xaxis_title='False positive rate',yaxis_title='True positive rate');chart(fig)
    with r:
        fig=go.Figure(go.Scatter(x=e['pr']['recall'],y=e['pr']['precision'],name='Selected model'));fig.add_hline(y=e['holdout_prevalence'],line_dash='dash');fig.update_layout(title='Holdout precision–recall',xaxis_title='Recall',yaxis_title='Precision');chart(fig)
    st.markdown('#### Confusion matrix · frozen threshold')
    cm=pd.DataFrame(e['confusion_matrix'],index=['Actual: no churn','Actual: churn'],columns=['Predicted: no churn','Predicted: churn'])
    st.dataframe(cm,use_container_width=True)
    st.markdown('#### Validation-only model selection')
    st.dataframe(pd.DataFrame(e['candidates']),hide_index=True,use_container_width=True)
    st.caption(f"Model selected by validation average precision. Threshold {m['threshold']:.2f} maximizes validation F1 on a prespecified 0.05–0.95 grid. Test set is untouched until final evaluation; model is not refitted afterward.")
    st.markdown('#### Coefficient associations')
    cf=pd.DataFrame(e['coefficients']).head(15).sort_values('coefficient')
    chart(px.bar(cf,x='coefficient',y='feature',orientation='h',color='coefficient',color_continuous_scale=['#627ef0','#68e7bd']))
    st.caption('Logistic coefficients are conditional log-odds associations. Numeric inputs are standardized; categoricals use full one-hot encoding with regularization, so there is no omitted reference category. Coefficients are not causal effects, individual explanations, or a fair ranking of business actions. Correlated features can redistribute coefficients.')
    st.download_button('Download evaluation evidence',__import__('json').dumps(e,indent=2),'evaluation.json','application/json')

with method:
    st.subheader('What the numbers mean')
    st.markdown('''
- **Churn rate:** source records labeled `Churn=Yes` divided by all records in the displayed sample/group. IBM’s related Cognos sample defines churn as leaving within the last month; the exact CSV has no timestamp for temporal validation.
- **Revenue at risk / weighted monthly exposure proxy:** sum of `predicted probability × MonthlyCharges` for uploaded/scored records. This is a ranking-oriented charge exposure proxy—not an empirically calibrated forecast of loss, annual revenue, savings, or a causal estimate.
- **CLV proxy / historical value proxy:** `tenure × current MonthlyCharges`. This approximates historical gross charges under a constant-price assumption. It is **not true CLV**, profit, discounted future value, or the source `TotalCharges` field.
- **Historical churned-group charge exposure:** sum of `MonthlyCharges` among sample records already labeled churned. Distinct from model-weighted exposure.
- **Review flag:** probability greater than or equal to the frozen validation-selected threshold. No intervention, contact, or decision is automated.
''')
    st.markdown('#### Boundaries and provenance')
    st.write('Source: IBM/telco-customer-churn-on-icp4d, pinned commit d5371f5. Repository license: Apache-2.0 for the code pattern; no separate dataset license was identified. Raw source records are excluded from this distribution. Related IBM Cognos documentation describes a fictional telco sample, but its enhanced XLSX/CLTV fields must not be assumed to be the same schema as this original CSV.')
    st.write('Excluded from model: customerID, gender, SeniorCitizen, Partner, Dependents. Excluding demographics does not establish fairness; contract, tenure, service and billing features may still act as proxies. No subgroup fairness or external validation has been established.')
    st.write('Missing source TotalCharges (11 rows) is median-imputed using training-only statistics. Inference deliberately rejects missing values, unknown categories, implausible ranges and inconsistent service combinations. Cross-sectional sample, limited provenance, unknown collection dates and possible feature timing leakage mean this is not verified prospective churn prediction.')
    st.write('There is no payment-delay variable, true CLV, treatment/outreach data, retention experiment, profitability model or demonstrated business savings. Probabilities were not independently calibrated. Real deployment requires feature-time audits, consent/security controls, calibration, fairness review, drift monitoring and prospective validation.')
    st.markdown('[IBM code pattern & CSV](https://github.com/IBM/telco-customer-churn-on-icp4d) · [Related IBM Cognos sample](https://www.ibm.com/docs/en/cognos-analytics/12.0.x?topic=samples-telco-customer-churn)')

st.divider()
st.caption('SIGNAL · Customer Churn Analytics · Reproducible portfolio demonstration · No customer IDs shipped')
