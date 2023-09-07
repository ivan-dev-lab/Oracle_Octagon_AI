import pandas as pd
from sklearn.preprocessing import StandardScaler
import logging

logging.basicConfig(level=logging.INFO, 
                    filename="logs/AI.log", 
                    filemode="w", 
                    format="%(asctime)s %(levelname)s %(message)s",
                    encoding="utf8")

logging.getLogger(__name__)

# fp_fighters - принимает путь до файла с данными о бойцах
# fp_fights - принимает путь до файла с данными о боях
# Вся статистика по бойцу из fp_fighters по FighterID переносится в train_df вместо столбца для FighterID из fp_fights
# Для большей наглядности, см. AI.md в GitHub
# Функция возвращает list с предобработанным X и Y

def preprocess (fp_fighters: str, fp_fights: str) -> list[pd.DataFrame]:
    logging.info(msg="Начат процесс предобработки данных")
    result = []
    
    train_list = []
    fighters_data = pd.read_csv(fp_fighters, index_col=[0])
    fights_data = pd.read_csv(fp_fights, index_col=[0])

    fighters_data.dropna(inplace=True)
    fights_data.dropna(inplace=True)

    fighters_data.drop(columns=["Division", "Name", "URL"], inplace=True)
    logging.info(msg="Удалены не имеющие значения данные")

    fights_data = fights_data[~fights_data["Result_2"].isin(['No Contest', 'TBD', 'ss'])]
    replacements = {
        'ПОБЕДА': 1,
        'Loss': 0,
        'Ничьих': 0.5
    }
    fights_data.replace(replacements, inplace=True)

    for i in range(len(fights_data.values)):
        train_dict = {}
        for column in fights_data:
            if column not in ["FightID", "URL"]:
                train_dict[column] = fights_data.iloc[i][column]  
            
        
        for j in range(1,2+1):
            FighterID = train_dict.pop(f"FighterID_{j}")
            Fighter_data = fighters_data[fighters_data["FighterID"] == FighterID]

            for _ in range(1,len(Fighter_data)+1):
                for column in Fighter_data:
                    if column != "FighterID":
                        train_dict[f"{column}_{j}"] = Fighter_data[column].values[0]
        
        train_list.append(train_dict)

    logging.info(msg="Закончено преобразование данных")
    
    train_df = pd.DataFrame(data=train_list)

    X = train_df.iloc[:, 2:].copy()
    Y = train_df.iloc[:, :2].copy()
    logging.info(msg="Данные разделены на X и Y")

    scaler = StandardScaler().fit(X)
    X_columns = X.columns
    X = pd.DataFrame(data=scaler.transform(X), columns=X_columns)
    logging.info(msg="Данные нормализованы")
    
    result.append(X)
    result.append(Y)

    logging.info(msg="Процесс предобработки данных завершен")
    return result