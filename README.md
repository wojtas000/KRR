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

### Insert statements
The insertion can be done either one by one or all together, with each statement in separate line:

1. ```initially ~car_washed and ~lawn_mowed and ~gift_bought```
2. ```WASH_CAR causes car_washed with time 30 minutes if ~car_washed```
3. ```MOW_LAWN causes lawn_mowed with time 75 minutes if ~lawn_mowed```
4. ```BUY_GIFT causes gift_bought with time 90 minutes if ~gift_bought```

### Query the system:

#### Executability query

``` necessary  executable  WASH_CAR,MOW_LAWN  from  ~car_washed and ~lawn_mowed and ~gift_bought ```

#### Executability query with time

``` necessary  executable  WASH_CAR,MOW_LAWN  with time  120 minutes  from  ~car_washed and ~lawn_mowed and ~gift_bought ```  

#### Value query

``` necessary  car_washed  after  GIFT_BOUGHT,MOW_LAWN  from  ~car_washed and ~lawn_mowed and ~gift_bought ```