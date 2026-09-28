# Attendance Predictor

Flask app that shows a student how many classes to attend to reach a target (default 90%), recover above a threshold (default 75%), how many they can safely miss, and their predicted end-of-semester attendance.

Thresholds and semester dates are **configurable app settings**, not claims about official policy. Currently runs on in-memory **sample data only**.

## Run
```
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py        # http://127.0.0.1:5000
```

## Configuration (environment variables)
`SEMESTER_START` (2026-08-29), `SEMESTER_END` (2026-11-29), `TARGET_PCT` (90), `DETENTION_PCT` (75), `UPCOMING_LIMIT` (10).

## Structure
- `app.py` - routes only
- `services/dataset_service.py` - data loading/validation (**future dataset integration goes here only**)
- `services/attendance_service.py` - percentage and state
- `services/prediction_service.py` - classes required, safe absences, projections

## Formulas
- Classes required: `x = ceil((T*total - 100*attended) / (100 - T))`
- Safe absences (remaining F): `floor(attended + F - thr*(total+F)/100)`
- Prediction: `(attended + F*rate) / (total + F)`

## Module 2: dataset ingestion
- `data/sample_timetable.csv` is loaded at startup. Upload your own at `/admin/upload` (localhost only, .csv/.xlsx/.xls, 5 MB max).
- Columns are matched by name (case/space/punctuation-insensitive, with aliases in `ALIASES`). Required: section, date, subject code or name. Optional: day, period, start/end time, faculty, room.
- Date format is detected from the data; ambiguous day/month order raises a warning (day-first is used).
- Invalid rows are never dropped silently: they are listed with row numbers and the dataset is not activated until fixed.
- Run tests: `python -m unittest discover -s tests -v`
- The Module 1 dashboard still reads `services/sample_data.py`; wiring it to the ingestion engine is a later module.
