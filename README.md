# KRR
Knowledge representation and reasoning

## Run
```bash
git clone https://github.com/wojtas000/KRR.git
cd KRR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Example 
Insert statements one by one:

1. ```initially ~car_washed and ~lawn_mowed and ~gift_bought and ~ready_for_party```
2. ```WASH_CAR causes car_washed with time 30 minutes```
3. ```MOW_LAWN causes lawn_mowed with time 75 minutes```
4. ```BUY_GIFT causes gift_bought with time 90 minutes```
5. ```GET_READY causes ready_for_party with time 45 minutes```
