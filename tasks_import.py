import win32clipboard
import json


def convert_to_dict():

    win32clipboard.OpenClipboard()
    tasks = win32clipboard.GetClipboardData().split("\r\n")
    win32clipboard.CloseClipboard()
    tasks_json = []
    sizes_convert_dict = {
        "35.5W": "3.5Y",
        "36W": "4Y",
        "36.5W": "4.5Y",
        "37.5W": "5Y",
        "38W": "5.5Y",
        "38.5W": "6Y",
        "39W": "6.5Y",
        "40W": "7Y",
        "40.5W": "7.5Y",
        "41W": "8Y",
        "42W": "8.5Y",
        "42.5W": "9Y",
        "43W": "9.5Y",
        "44W": "10Y",
        "44.5W": "10.5Y",
        "40": "7",
        "40.5": "7.5",
        "41": "8",
        "42": "8.5",
        "42.5": "9",
        "43": "9.5",
        "44": "10",
        "44.5": "10.5",
        "45": "11",
        "45.5": "11.5",
        "46": "12",
        "47": "12.5",
        "47.5": "13",
        "48": "13.5",
        "48.5": "14",
        "49.5": "15"

    }
    try:
        for i in range(len(tasks)):
            row = tasks[i].split("\t")
            task = {
                "id": f"{i+1}".strip(),
                "sku": row[0].strip().lower(),
                "size": sizes_convert_dict[row[1].strip()],
                "webhook_url": row[2].strip(),
                "bypass": row[3].strip().lower(),
                "product_url": row[4].strip(),
            }
            tasks_json.append(task)

        with open("USER_DATA/tasks.json", "w") as file:
            json.dump(tasks_json, file)
    except Exception as error:
        print(f'Task import error: {error}')


convert_to_dict()

