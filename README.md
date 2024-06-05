# KRR
Knowledge representation and reasoning

## Run

Clone repository:

```bash
git clone https://github.com/wojtas000/KRR.git
cd KRR
```

If you want to create separate virtual environment (Linux):
```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies and run the application:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Insert statements 

### Allowed statements

1. **initially** (formula)
2. (action) **causes** (effect formula) **if** (precondition formula)
3. (action) **releases** (fluent) **if** (precondition formula)
4. (action) **lasts** (time)
5. (effect formula) **after** (action)
6. **always** (formula)
7. **impossible** (formula)

### Allowed logical operators:

1. and, &
2. or, |
3. implies, =>
4. iff, <=>
5. brackets () to separate subformulas

### Example

The insertion can be done either one by one or all together, with each statement in separate line:

1. ```initially ~car_washed and ~lawn_mowed and ~gift_bought```
2. ```WASH_CAR causes car_washed if ~car_washed```
3. ```MOW_LAWN causes lawn_mowed if ~lawn_mowed```
4. ```BUY_GIFT causes gift_bought if ~gift_bought```
5. ```WASH_CAR lasts 30```
6. ```MOW_LAWN lasts 45```
7. ```BUY_GIFT lasts 90```

## Query language

### Examples

#### Executability query

``` necessary executable WASH_CAR,MOW_LAWN from ~car_washed and ~lawn_mowed and ~gift_bought ```

#### Executability query with time

``` necessary executable WASH_CAR,MOW_LAWN with time 120 from ~car_washed and ~lawn_mowed and ~gift_bought ```  

#### Value query

``` necessary car_washed after GIFT_BOUGHT,MOW_LAWN from ~car_washed and ~lawn_mowed and ~gift_bought ```
