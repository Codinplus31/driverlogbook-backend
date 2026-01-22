# Django Project Setup Guide

This README explains how to initialize and run this Django project locally.

---

##  Prerequisites

Make sure you have the following installed on your system:

* Python 3.8 or higher
* pip (comes with Python)
* Git

Check versions:

```bash
python --version
pip --version
```

---

##  Clone the Repository

```bash
git clone https://github.com/Codinplus31/driverlogbook-backend.git
cd driverlogbook-backend
```

---

##  Create & Activate a Virtual Environment (Recommended)

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

---

## 📄 Install Dependencies

Install all required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Verify Django installation:

```bash
django-admin --version
```

---


---

## ▶️ Start the Development Server

```bash
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000/
```

---


## ❗ Common Issues

### `ModuleNotFoundError`

Make sure:

* Virtual environment is activated
* All packages are installed:

```bash
pip install -r requirements.txt
```

---

## 📌 Notes

* Always activate the virtual environment before running Django commands

