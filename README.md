ENV=prod flask db upgrade
adb reverse tcp:8000 tcp:8000
