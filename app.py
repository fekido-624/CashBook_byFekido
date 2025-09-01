

# Helper for categories file path
def get_buku_categories_file_for(username, buku_akaun):
    user_dir = os.path.join('User', username)
    return os.path.join(user_dir, f"categories_{username}_{buku_akaun}.txt")


# --- Config untuk Email (Gmail SMTP) ---










# --- Config untuk Email (Gmail SMTP) ---
EMAIL_SENDER = 'your_gmail@gmail.com'  # Gantikan dengan email Gmail anda
EMAIL_PASSWORD = 'your_gmail_app_password'  # Gantikan dengan App Password Gmail (bukan password biasa)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



from flask import Flask, render_template, request, redirect, url_for, flash, session
import csv
# ...existing code...
import os
from datetime import datetime

# ...existing code...
app = Flask(__name__)
app.secret_key = 'cashbook_secret'  # Untuk flash message & session
app.permanent_session_lifetime = 120  # 2 minit dalam saat
CSV_FILE = 'cashbook.csv'
CATEGORIES_FILE = 'categories.txt'
USERS_FILE = 'users.txt'  # Simpan username:password
BUKU_FILE = 'buku_akaun.txt'  # Simpan buku akaun per user

# Edit Nama Buku Akaun
@app.route('/edit_buku/<old_buku>', methods=['GET', 'POST'])
def edit_buku(old_buku):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    buku_list = read_buku_akaun(username)
    if old_buku not in buku_list:
        flash('Buku akaun tidak dijumpai.', 'danger')
        return redirect(url_for('senarai_buku'))
    if request.method == 'POST':
        new_buku = request.form.get('nama_buku_baru', '').strip()
        if not new_buku:
            flash('Nama buku akaun baru tidak boleh kosong.', 'danger')
            return redirect(url_for('edit_buku', old_buku=old_buku))
        if new_buku in buku_list:
            flash('Nama buku akaun sudah wujud.', 'danger')
            return redirect(url_for('edit_buku', old_buku=old_buku))
        # Update buku_akaun.txt
        with open(BUKU_FILE, encoding='utf-8') as f:
            lines = f.readlines()
        with open(BUKU_FILE, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip() == f'{username}:{old_buku}':
                    f.write(f'{username}:{new_buku}\n')
                else:
                    f.write(line)
        # Update all transactions in cashbook.csv
        all_tx = read_transactions()
        for t in all_tx:
            if t.get('username') == username and t.get('buku_akaun') == old_buku:
                t['buku_akaun'] = new_buku
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['username', 'buku_akaun', 'tarikh', 'jenis', 'amaun', 'kategori', 'nota'])
            writer.writeheader()
            for t in all_tx:
                writer.writerow(t)
        # Rename categories file if exists
        old_cat = get_buku_categories_file_for(username, old_buku)
        new_cat = get_buku_categories_file_for(username, new_buku)
        if old_cat and os.path.exists(old_cat):
            os.rename(old_cat, new_cat)
        flash('Nama buku akaun berjaya dikemaskini.', 'success')
        return redirect(url_for('senarai_buku'))
    return render_template('edit_buku.html', old_buku=old_buku)

# --- Lupa Password ---
@app.route('/lupa_password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('Sila masukkan email anda.', 'danger')
            return redirect(url_for('lupa_password'))
        # Cari user dalam users.csv
        user_row = None
        with open(USERS_CSV, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'] == email:
                    user_row = row
                    break
        if not user_row:
            flash('Email tidak dijumpai.', 'danger')
            return redirect(url_for('lupa_password'))
        # Hantar email
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_SENDER
            msg['To'] = email
            msg['Subject'] = 'Reset Password Cashbook'
            body = f"""Assalamualaikum,\n\nBerikut adalah maklumat login Cashbook anda:\n\nUsername: {user_row['username']}\nPassword: {user_row['password']}\n\nSila login di sistem Cashbook seperti biasa.\n\nTerima kasih."""
            msg.attach(MIMEText(body, 'plain'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, email, msg.as_string())
            server.quit()
            flash('Maklumat login telah dihantar ke email anda.', 'success')
        except Exception as e:
            flash(f'Gagal hantar email: {e}', 'danger')
        return redirect(url_for('login'))
    return render_template('lupa_password.html')

# --- Pendaftaran Pengguna Baru ---
USERS_CSV = 'users.csv'
if not os.path.exists(USERS_CSV):
    with open(USERS_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'email', 'password', 'phone'])

def is_unique_user(username, email, phone):
    with open(USERS_CSV, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username or row['email'] == email or row['phone'] == phone:
                return False
    return True

def save_user(username, email, password, phone):
    with open(USERS_CSV, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([username, email, password, phone])
    # Create user folder
    user_dir = os.path.join('User', username)
    os.makedirs(user_dir, exist_ok=True)

@app.route('/daftar_pengguna', methods=['POST'])
def daftar_pengguna():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    phone = request.form.get('phone', '').strip()
    if not (username and email and password and phone):
        flash('Semua maklumat diperlukan.', 'danger')
        return redirect(url_for('login'))
    if not is_unique_user(username, email, phone):
        flash('Username, email, atau no. telefon telah digunakan.', 'danger')
        return redirect(url_for('login'))
    save_user(username, email, password, phone)
    flash('Pendaftaran berjaya! Sila login.', 'success')
    return redirect(url_for('login'))

# Dummy user untuk demo (username: admin, password: admin)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        f.write('admin:admin\n')

# Pastikan fail CSV wujud dan ada header (tambah username, buku_akaun)
try:
    with open(CSV_FILE, 'x', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'buku_akaun', 'tarikh', 'jenis', 'amaun', 'kategori', 'nota'])
except FileExistsError:
    pass

# Pastikan fail buku akaun wujud
if not os.path.exists(BUKU_FILE):
    with open(BUKU_FILE, 'w', encoding='utf-8') as f:
        pass

# --- Kemaskini Profil Pengguna ---
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        flash('Sila login dahulu.', 'danger')
        return redirect(url_for('login'))
    old_username = session['username']
    new_username = request.form.get('username', '').strip()
    new_email = request.form.get('email', '').strip()
    new_password = request.form.get('password', '').strip()
    new_phone = request.form.get('phone', '').strip()
    if not (new_username and new_email and new_phone):
        flash('Semua maklumat diperlukan (kecuali password jika tidak mahu tukar).', 'danger')
        return redirect(url_for('senarai_buku'))
    # Baca semua user
    users = []
    with open(USERS_CSV, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    # Semak unik (kecuali untuk user sendiri)
    for row in users:
        if row['username'] == new_username and row['username'] != old_username:
            flash('Username telah digunakan.', 'danger')
            return redirect(url_for('senarai_buku'))
        if row['email'] == new_email and row['username'] != old_username:
            flash('Email telah digunakan.', 'danger')
            return redirect(url_for('senarai_buku'))
        if row['phone'] == new_phone and row['username'] != old_username:
            flash('No. telefon telah digunakan.', 'danger')
            return redirect(url_for('senarai_buku'))
    # Update user
    updated = False
    for row in users:
        if row['username'] == old_username:
            row['username'] = new_username
            row['email'] = new_email
            row['phone'] = new_phone
            if new_password:
                row['password'] = new_password
            updated = True
            break
    if not updated:
        flash('Pengguna tidak dijumpai.', 'danger')
        return redirect(url_for('senarai_buku'))
    # Tulis semula users.csv
    with open(USERS_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['username', 'email', 'password', 'phone'])
        writer.writeheader()
        for row in users:
            writer.writerow(row)
    # Update session
    session['username'] = new_username
    session['email'] = new_email
    session['phone'] = new_phone
    flash('Profil berjaya dikemaskini.', 'success')
    return redirect(url_for('senarai_buku'))

def read_users():
    users = {}
    with open(USERS_FILE, encoding='utf-8') as f:
        for line in f:
            if ':' in line:
                u, p = line.strip().split(':', 1)
                users[u] = p
    return users


def read_transactions():
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_transaction(data):
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(data)

# Buku akaun helpers
def read_buku_akaun(username):
    buku = []
    with open(BUKU_FILE, encoding='utf-8') as f:
        for line in f:
            if ':' in line:
                u, b = line.strip().split(':', 1)
                if u == username:
                    buku.append(b)
    return buku

def add_buku_akaun(username, nama_buku):
    buku = read_buku_akaun(username)
    if nama_buku and nama_buku not in buku:
        with open(BUKU_FILE, 'a', encoding='utf-8') as f:
            f.write(f'{username}:{nama_buku}\n')
        return True
    return False

def delete_buku_akaun(username, nama_buku):
    buku = read_buku_akaun(username)
    if nama_buku not in buku:
        return False
    # Padam baris dari fail
    with open(BUKU_FILE, encoding='utf-8') as f:
        lines = f.readlines()
    with open(BUKU_FILE, 'w', encoding='utf-8') as f:
        for line in lines:
            if not (line.strip() == f'{username}:{nama_buku}'):
                f.write(line)
    return True

def get_buku_categories_file():
    if 'username' not in session or 'buku_akaun' not in session:
        return None
    username = session['username']
    buku_akaun = session['buku_akaun']
    user_dir = os.path.join('User', username)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, f"categories_{username}_{buku_akaun}.txt")

def read_categories():
    filename = get_buku_categories_file()
    if not filename or not os.path.exists(filename):
        return []
    with open(filename, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def add_category(new_cat):
    cats = read_categories()
    filename = get_buku_categories_file()
    if new_cat and new_cat not in cats:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(new_cat + '\n')

def filter_transactions(transactions, tarikh, kategori, jenis, username, buku_akaun):
    # Hanya proses transaksi yang ada field 'username' dan 'buku_akaun'
    result = [t for t in transactions if t.get('username') == username and t.get('buku_akaun') == buku_akaun]
    if tarikh:
        result = [t for t in result if t['tarikh'] == tarikh]
    if kategori:
        # kategori boleh jadi list (multi-select) atau string (single)
        if isinstance(kategori, list) and kategori:
            result = [t for t in result if t['kategori'] in kategori]
        elif isinstance(kategori, str) and kategori:
            result = [t for t in result if t['kategori'] == kategori]
    if jenis:
        result = [t for t in result if t['jenis'] == jenis]
    return result


# Login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        session.permanent = True
        return redirect(url_for('senarai_buku'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Semak dari users.csv
        found = False
        with open(USERS_CSV, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['username'] == username and row['password'] == password:
                    session['username'] = username
                    session['email'] = row['email']
                    session['phone'] = row['phone']
                    found = True
                    break
        if found:
            session.permanent = True
            flash('Login berjaya!', 'success')
            return redirect(url_for('senarai_buku'))
        else:
            flash('Username atau password salah!', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('buku_akaun', None)
    flash('Logout berjaya.', 'success')
    return redirect(url_for('login'))


# Senarai buku akaun page
@app.route('/senarai_buku', methods=['GET', 'POST'])
def senarai_buku():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    senarai_buku = read_buku_akaun(username)
    return render_template('senarai_buku.html', senarai_buku=senarai_buku)

@app.route('/export_buku_akaun/', defaults={'buku_akaun': ''})
@app.route('/export_buku_akaun/<buku_akaun>')
def export_buku_akaun(buku_akaun):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    if not buku_akaun:
        # Export semua data user
        transactions = [t for t in read_transactions() if t.get('username') == username]
        filename = f"{username}_semua_buku_export.csv"
    else:
        transactions = [t for t in read_transactions() if t.get('username') == username and t.get('buku_akaun') == buku_akaun]
        filename = f"{username}_{buku_akaun}_export.csv"
    if not transactions:
        flash('Tiada data untuk diexport.', 'danger')
        return redirect(url_for('senarai_buku'))
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['username', 'buku_akaun', 'tarikh', 'jenis', 'amaun', 'kategori', 'nota'])
    writer.writeheader()
    for t in transactions:
        writer.writerow(t)
    output.seek(0)
    from flask import Response
    return Response(output.getvalue(), mimetype='text/csv', headers={"Content-Disposition": f"attachment;filename={filename}"})

@app.route('/import_buku_akaun/<buku_akaun>', methods=['POST'])
def import_buku_akaun(buku_akaun):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    file = request.files.get('import_file')
    if not file or not file.filename.endswith('.csv'):
        flash('Sila pilih fail CSV yang sah.', 'danger')
        return redirect(url_for('senarai_buku'))
    import io
    stream = io.StringIO(file.stream.read().decode('utf-8'))
    reader = csv.DictReader(stream)
    new_rows = []
    for row in reader:
        # Only import rows for this user and buku_akaun
        if row.get('username') == username and row.get('buku_akaun') == buku_akaun:
            new_rows.append(row)
    if not new_rows:
        flash('Tiada data sesuai dalam fail.', 'danger')
        return redirect(url_for('senarai_buku'))
    # Remove old rows for this user & buku_akaun, then append new
    all_tx = read_transactions()
    all_tx = [t for t in all_tx if not (t.get('username') == username and t.get('buku_akaun') == buku_akaun)]
    all_tx.extend(new_rows)
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['username', 'buku_akaun', 'tarikh', 'jenis', 'amaun', 'kategori', 'nota'])
        writer.writeheader()
        for t in all_tx:
            writer.writerow(t)
    flash('Data buku akaun berjaya diimport.', 'success')
    return redirect(url_for('senarai_buku'))
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    senarai_buku = read_buku_akaun(username)
    return render_template('senarai_buku.html', senarai_buku=senarai_buku)

# Tambah buku akaun
@app.route('/tambah_buku', methods=['POST'])
def tambah_buku():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    nama_buku = request.form.get('buku_akaun_baru', '').strip()
    if nama_buku:
        if add_buku_akaun(username, nama_buku):
            flash(f"Buku akaun '{nama_buku}' berjaya ditambah.", 'success')
        else:
            flash(f"Buku akaun '{nama_buku}' sudah wujud.", 'danger')
    else:
        flash('Nama buku akaun tidak boleh kosong.', 'danger')
    return redirect(url_for('senarai_buku'))

# Padam buku akaun
@app.route('/padam_buku/<buku_akaun>', methods=['GET'])
def padam_buku(buku_akaun):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    confirm_buku = request.args.get('confirm_buku', '')
    if confirm_buku != buku_akaun:
        flash('Sila taip nama buku akaun dengan tepat untuk sahkan padam.', 'danger')
        return redirect(url_for('senarai_buku'))
    # Padam semua transaksi berkaitan buku akaun ini
    all_tx = read_transactions()
    all_tx = [t for t in all_tx if not (t.get('username') == username and t.get('buku_akaun') == buku_akaun)]
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['username', 'buku_akaun', 'tarikh', 'jenis', 'amaun', 'kategori', 'nota'])
        writer.writeheader()
        for t in all_tx:
            writer.writerow(t)
    # Padam buku akaun dari senarai
    if delete_buku_akaun(username, buku_akaun):
        flash(f"Buku akaun '{buku_akaun}' dan semua transaksinya berjaya dipadam.", 'success')
    else:
        flash('Buku akaun tidak dijumpai.', 'danger')
    return redirect(url_for('senarai_buku'))
 # Pilih buku akaun dan masuk ke cashbook
@app.route('/buku_akaun/<buku_akaun>', methods=['GET', 'POST'])
def buku_akaun(buku_akaun):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    # Pastikan buku_akaun memang milik user login
    if buku_akaun not in read_buku_akaun(username):
        flash('Akses tidak dibenarkan ke buku akaun ini.', 'danger')
        return redirect(url_for('senarai_buku'))
    session['buku_akaun'] = buku_akaun
    categories = read_categories()
    if request.method == 'POST':
        tarikh = request.form['tarikh']
        jenis = request.form['jenis']
        amaun = request.form['amaun']
        kategori = request.form['kategori']
        nota = request.form['nota']
        write_transaction([username, buku_akaun, tarikh, jenis, amaun, kategori, nota])
        flash('Transaksi berjaya ditambah.', 'success')
        return redirect(url_for('buku_akaun', buku_akaun=buku_akaun))
    # Filter params
    filter_tarikh = request.args.get('filter_tarikh', '')
    filter_kategori = request.args.getlist('filter_kategori')
    filter_jenis = request.args.get('filter_jenis', '')
    page = int(request.args.get('page', 1))
    per_page = 10
    transactions = read_transactions()
    filtered = filter_transactions(transactions, filter_tarikh, filter_kategori, filter_jenis, username, buku_akaun)
    total_masuk = sum(float(t['amaun']) for t in filtered if t['jenis'] == 'masuk')
    total_keluar = sum(float(t['amaun']) for t in filtered if t['jenis'] == 'keluar')
    baki = total_masuk - total_keluar
    # Paging
    total_tx = len(filtered)
    start = (page-1)*per_page
    end = start+per_page
    paged_tx = filtered[start:end]
    total_pages = (total_tx + per_page - 1) // per_page
    return render_template('buku_akaun.html', transactions=paged_tx, total_masuk=total_masuk, total_keluar=total_keluar, baki=baki, categories=categories, filter_tarikh=filter_tarikh, filter_kategori=filter_kategori, filter_jenis=filter_jenis, current_date=datetime.now().strftime('%Y-%m-%d'), buku_akaun=buku_akaun, page=page, total_pages=total_pages)


# Kategori routes (perlu update url_for jika guna pada cashbook)
@app.route('/delete_kategori/<cat>/<buku_akaun>')
def delete_kategori(cat, buku_akaun):
    cat = cat.strip()
    if delete_category(cat):
        flash(f"Kategori '{cat}' berjaya dipadam.", 'success')
    else:
        flash(f"Kategori '{cat}' tidak boleh dipadam kerana masih digunakan dalam transaksi.", 'danger')
    return redirect(url_for('buku_akaun', buku_akaun=buku_akaun))

@app.route('/add_kategori/<buku_akaun>', methods=['POST'])
def add_kategori(buku_akaun):
    kategori_baru = request.form.get('kategori_baru', '').strip()
    if kategori_baru:
        add_category(kategori_baru)
        flash(f"Kategori '{kategori_baru}' berjaya ditambah.", 'success')
    else:
        flash("Nama kategori tidak boleh kosong.", 'danger')
    return redirect(url_for('buku_akaun', buku_akaun=buku_akaun))

 
@app.route('/edit/<int:idx>/<buku_akaun>', methods=['GET', 'POST'])
def edit_transaction(idx, buku_akaun):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    # Pastikan buku_akaun memang milik user login
    if buku_akaun not in read_buku_akaun(username):
        flash('Akses tidak dibenarkan ke buku akaun ini.', 'danger')
        return redirect(url_for('senarai_buku'))
    categories = read_categories()
    transaksi = get_transaction_by_index(idx, buku_akaun)
    if not transaksi:
        flash('Transaksi tidak dijumpai.', 'danger')
        return redirect(url_for('buku_akaun', buku_akaun=buku_akaun))
    if request.method == 'POST':
        tarikh = request.form['tarikh']
        jenis = request.form['jenis']
        amaun = request.form['amaun']
        kategori = request.form['kategori']
        nota = request.form['nota']
        new_data = {'tarikh': tarikh, 'jenis': jenis, 'amaun': amaun, 'kategori': kategori, 'nota': nota}
        update_transaction(idx, new_data, buku_akaun)
        flash('Transaksi berjaya dikemaskini.', 'success')
        return redirect(url_for('buku_akaun', buku_akaun=buku_akaun))
    return render_template('edit.html', transaksi=transaksi, idx=idx, categories=categories, buku_akaun=buku_akaun)

 
@app.route('/delete/<int:idx>/<buku_akaun>')
def delete_transaction_route(idx, buku_akaun):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    # Pastikan buku_akaun memang milik user login
    if buku_akaun not in read_buku_akaun(username):
        flash('Akses tidak dibenarkan ke buku akaun ini.', 'danger')
        return redirect(url_for('senarai_buku'))
    if delete_transaction(idx, buku_akaun):
        flash('Transaksi berjaya dipadam.', 'success')
    else:
        flash('Transaksi tidak dijumpai.', 'danger')
    return redirect(url_for('buku_akaun', buku_akaun=buku_akaun))

def delete_category(cat):
    username = session.get('username')
    buku_akaun = session.get('buku_akaun')
    transactions = read_transactions()
    # Hanya block jika kategori digunakan dalam buku akaun semasa
    if any(t.get('kategori') == cat and t.get('username') == username and t.get('buku_akaun') == buku_akaun for t in transactions):
        return False
    cats = read_categories()
    cats = [c for c in cats if c != cat]
    filename = get_buku_categories_file()
    with open(filename, 'w', encoding='utf-8') as f:
        for c in cats:
            f.write(c + '\n')
    return True


def get_transaction_by_index(idx, buku_akaun):
    username = session.get('username')
    transactions = [t for t in read_transactions() if t.get('username') == username and t.get('buku_akaun') == buku_akaun]
    if 0 <= idx < len(transactions):
        return transactions[idx]
    return None

def update_transaction(idx, new_data, buku_akaun):
    username = session.get('username')
    all_tx = read_transactions()
    user_tx = [t for t in all_tx if t.get('username') == username and t.get('buku_akaun') == buku_akaun]
    if 0 <= idx < len(user_tx):
        user_indices = [i for i, t in enumerate(all_tx) if t.get('username') == username and t.get('buku_akaun') == buku_akaun]
        real_idx = user_indices[idx]
        new_data_full = {'username': username, 'buku_akaun': buku_akaun, **new_data}
        all_tx[real_idx] = new_data_full
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['username', 'buku_akaun', 'tarikh', 'jenis', 'amaun', 'kategori', 'nota'])
            writer.writeheader()
            for t in all_tx:
                writer.writerow(t)
        return True
    return False

def delete_transaction(idx, buku_akaun):
    username = session.get('username')
    all_tx = read_transactions()
    user_tx = [t for t in all_tx if t.get('username') == username and t.get('buku_akaun') == buku_akaun]
    if 0 <= idx < len(user_tx):
        user_indices = [i for i, t in enumerate(all_tx) if t.get('username') == username and t.get('buku_akaun') == buku_akaun]
        real_idx = user_indices[idx]
        all_tx.pop(real_idx)
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['username', 'buku_akaun', 'tarikh', 'jenis', 'amaun', 'kategori', 'nota'])
            writer.writeheader()
            for t in all_tx:
                writer.writerow(t)
        return True
    return False


# --- Admin Download/Upload CSV (Backup/Restore) ---
from flask import send_file, request
import os

def is_admin():
    return session.get('username') == 'fekido'

@app.route('/admin/users')
def admin_view_users():
    if not is_admin():
        return 'Unauthorized', 403
    users = []
    with open('users.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return render_template('admin_users.html', users=users)
@app.route('/admin/export_all')
def admin_export_all():
    if not is_admin():
        return 'Unauthorized', 403
    import zipfile, io
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in ['users.csv', 'cashbook.csv']:
            if os.path.exists(fname):
                zf.write(fname)
    mem_zip.seek(0)
    from flask import send_file
    return send_file(mem_zip, mimetype='application/zip', as_attachment=True, download_name='all_data.zip')

@app.route('/admin/import_all', methods=['GET', 'POST'])
def admin_import_all():
    if not is_admin():
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files.get('import_file')
        if not file or not file.filename.endswith('.zip'):
            return 'Sila upload fail ZIP yang sah.', 400
        import zipfile, io
        with zipfile.ZipFile(io.BytesIO(file.read())) as zf:
            for fname in ['users.csv', 'cashbook.csv']:
                if fname in zf.namelist():
                    with open(fname, 'wb') as f:
                        f.write(zf.read(fname))
        return 'Data berjaya diimport! <a href="/admin/users">Kembali</a>'
    return render_template('admin_import_all.html')
    if not is_admin():
        return 'Unauthorized', 403
    users = []
    with open('users.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return render_template('admin_users.html', users=users)

@app.route('/admin/edit_user/<username>', methods=['GET', 'POST'])
def admin_edit_user(username):
    if not is_admin():
        return 'Unauthorized', 403
    users = []
    user_row = None
    with open('users.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                user_row = row.copy()
            users.append(row)
    if not user_row:
        flash('User tidak dijumpai.', 'danger')
        return redirect(url_for('admin_view_users'))
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '').strip()
        new_phone = request.form.get('phone', '').strip()
        # Check for uniqueness (except for this user)
        for row in users:
            if row['username'] == new_username and row['username'] != username:
                flash('Username telah digunakan.', 'danger')
                return redirect(url_for('admin_edit_user', username=username))
            if row['email'] == new_email and row['username'] != username:
                flash('Email telah digunakan.', 'danger')
                return redirect(url_for('admin_edit_user', username=username))
            if row['phone'] == new_phone and row['username'] != username:
                flash('No. telefon telah digunakan.', 'danger')
                return redirect(url_for('admin_edit_user', username=username))
        # Update user
        for row in users:
            if row['username'] == username:
                row['username'] = new_username
                row['email'] = new_email
                row['phone'] = new_phone
                if new_password:
                    row['password'] = new_password
                break
        # Write back to CSV
        with open('users.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['username', 'email', 'password', 'phone'])
            writer.writeheader()
            for row in users:
                writer.writerow(row)
        flash('User berjaya dikemaskini.', 'success')
        return redirect(url_for('admin_view_users'))
    return render_template('admin_edit_user.html', user=user_row)
    if not is_admin():
        return 'Unauthorized', 403
    users = []
    with open('users.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return render_template('admin_users.html', users=users)

@app.route('/admin/delete_user/<username>', methods=['POST'])
def admin_delete_user(username):
    if not is_admin():
        return 'Unauthorized', 403
    users = []
    deleted = False
    with open('users.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] != username:
                users.append(row)
            else:
                deleted = True
    with open('users.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['username', 'email', 'password', 'phone'])
        writer.writeheader()
        for row in users:
            writer.writerow(row)
    if deleted:
        flash(f'User {username} deleted.', 'success')
    else:
        flash(f'User {username} not found.', 'danger')
    return redirect(url_for('admin_view_users'))
    return session.get('username') == 'fekido'

@app.route('/admin/download/<filename>')
def admin_download_csv(filename):
    if not is_admin():
        return 'Unauthorized', 403
    if filename not in ['users.csv', 'cashbook.csv']:
        return 'Not allowed', 403
    if not os.path.exists(filename):
        return 'File not found', 404
    return send_file(filename, as_attachment=True)

@app.route('/admin/upload/<filename>', methods=['GET', 'POST'])
def admin_upload_csv(filename):
    if not is_admin():
        return 'Unauthorized', 403
    if filename not in ['users.csv', 'cashbook.csv']:
        return 'Not allowed', 403
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            file.save(filename)
            return f'{filename} uploaded successfully! <a href="/admin/upload/{filename}">Back</a>'
        return 'No file uploaded', 400
    return f'''
        <h3>Upload {filename}</h3>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button type="submit">Upload</button>
        </form>
        <a href="/">Back to app</a>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
