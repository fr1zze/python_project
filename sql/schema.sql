-- Структура базы системы учёта заявок на командировки.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    position TEXT NOT NULL CHECK (length(trim(position)) > 0)
);

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY,
    destination TEXT NOT NULL
        CHECK (length(trim(destination)) > 0),
    purpose TEXT NOT NULL
        CHECK (length(trim(purpose)) > 0),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    travel_cost REAL NOT NULL CHECK (travel_cost >= 0),
    hotel_cost REAL NOT NULL CHECK (hotel_cost >= 0),
    daily_allowance REAL NOT NULL CHECK (daily_allowance >= 0),
    CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS travel_requests (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    trip_id INTEGER NOT NULL UNIQUE,
    budget_limit REAL NOT NULL CHECK (budget_limit >= 0),

    FOREIGN KEY (employee_id)
        REFERENCES employees(id),

    FOREIGN KEY (trip_id)
        REFERENCES trips(id)
);

CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'на рассмотрении',

    CHECK (
        status IN (
            'на рассмотрении',
            'одобрена',
            'отклонена',
            'отменена'
        )
    ),

    FOREIGN KEY (request_id)
        REFERENCES travel_requests(id)
);