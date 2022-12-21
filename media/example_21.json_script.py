question1 = "Which one is correct team name in NBA?"
question1 = question1.upper()
data = {"question1": question1, }

import json
print(json.dumps(data))
