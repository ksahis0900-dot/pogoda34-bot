import os
import glob

files = glob.glob("images/*.jpg")
for f in files:
    filename = os.path.basename(f)
    new_name = None
    
    if filename.startswith("1В"): new_name = "volgograd.jpg"
    elif filename.startswith("2В"): new_name = "volzhsky.jpg"
    elif filename.startswith("3К"): new_name = "kamyshin.jpg"
    elif filename.startswith("4М"): new_name = "mikhaylovka.jpg"
    elif filename.startswith("5У"): new_name = "uryupinsk.jpg"
    elif filename.startswith("6Ф"): new_name = "frolovo.jpg"
    elif filename.startswith("7К"): new_name = "kalach.jpg"
    elif filename.startswith("8К"): new_name = "kotelnikovo.jpg"
    elif filename.startswith("9К"): new_name = "kotovo.jpg"
    elif filename.startswith("10С"): new_name = "surovikino.jpg"
    elif filename.startswith("11К"): new_name = "krasnoslobodsk.jpg"
    elif filename.startswith("12Ж"): new_name = "zhirnovsk.jpg"
    elif filename.startswith("13Н"): new_name = "novoanninsky.jpg"
    elif filename.startswith("14П"): new_name = "pallasovka.jpg"
    elif filename.startswith("15Д"): new_name = "dubovka.jpg"
    elif filename.startswith("16Н"): new_name = "nikolaevsk.jpg"
    elif filename.startswith("17Л"): new_name = "leninsk.jpg"
    elif filename.startswith("18П"): new_name = "petrov_val.jpg"
    elif filename.startswith("19С"): new_name = "serafimovich.jpg"
    
    if new_name:
        try:
            os.rename(f, os.path.join("images", new_name))
            print(f"Renamed {f} -> {new_name}")
        except Exception as e:
            print(f"Error renaming {f}: {e}")
