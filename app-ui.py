import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

DB_PATH = "kredit.db"


def tentukan_kelayakan(
        pendapatan,
        jumlah_pinjaman,
        pekerjaan_stabil,
        skor_slik,
        jaminan
    ):

    rasio = jumlah_pinjaman / pendapatan if pendapatan > 0 else 0

    if skor_slik == 5:
        return "RESIKO", rasio, "SLIK macet"

    if rasio <= 3 and skor_slik <= 2 and pekerjaan_stabil is True:
        return "GOOD", rasio, "Risiko rendah"

    if rasio <= 5 and skor_slik <= 3 and (pekerjaan_stabil is True or jaminan is True):
        return "MODERATE", rasio, "Risiko sedang"

    return "RESIKO", rasio, "Risiko tinggi"


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def normalize_bool(value):
    if isinstance(value, str):
        return value.strip().lower() == "ya"
    return bool(value)


def render_status_badge(status: str) -> str:
    color = "#9e9e9e"
    bg = "#eeeeee"
    if status == "GOOD":
        color = "#1b5e20"
        bg = "#c8e6c9"
    elif status == "MODERATE":
        color = "#f57f17"
        bg = "#fff9c4"
    elif status == "RESIKO":
        color = "#b71c1c"
        bg = "#ffcdd2"
    return (
        "<span style='font-weight:600;color:"
        + color
        + ";background:"
        + bg
        + ";padding:2px 8px;border-radius:12px;display:inline-block'>"
        + status
        + "</span>"
    )


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nasabah (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                pendapatan REAL NOT NULL,
                jumlah_pinjaman REAL NOT NULL,
                pekerjaan_stabil INTEGER NOT NULL CHECK(pekerjaan_stabil IN (0,1)),
                skor_slik INTEGER NOT NULL CHECK(skor_slik BETWEEN 1 AND 5),
                jaminan INTEGER NOT NULL CHECK(jaminan IN (0,1)),
                rasio REAL NOT NULL,
                kelayakan TEXT NOT NULL,
                alasan TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        info = conn.execute("PRAGMA table_info(nasabah)").fetchall()
        col_types = {row[1]: (row[2] or "").upper() for row in info}
        needs_migration = col_types.get("pekerjaan_stabil") == "TEXT" or col_types.get("jaminan") == "TEXT"
        if needs_migration:
            conn.execute(
                """
                CREATE TABLE nasabah_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT NOT NULL,
                    pendapatan REAL NOT NULL,
                    jumlah_pinjaman REAL NOT NULL,
                    pekerjaan_stabil INTEGER NOT NULL CHECK(pekerjaan_stabil IN (0,1)),
                    skor_slik INTEGER NOT NULL CHECK(skor_slik BETWEEN 1 AND 5),
                    jaminan INTEGER NOT NULL CHECK(jaminan IN (0,1)),
                    rasio REAL NOT NULL,
                    kelayakan TEXT NOT NULL,
                    alasan TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO nasabah_new (
                    id, nama, pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan,
                    rasio, kelayakan, alasan, created_at, updated_at
                )
                SELECT
                    id,
                    nama,
                    pendapatan,
                    jumlah_pinjaman,
                    CASE
                        WHEN pekerjaan_stabil IN ('ya','YA','1','true','TRUE') THEN 1
                        ELSE 0
                    END AS pekerjaan_stabil,
                    skor_slik,
                    CASE
                        WHEN jaminan IN ('ya','YA','1','true','TRUE') THEN 1
                        ELSE 0
                    END AS jaminan,
                    rasio,
                    kelayakan,
                    alasan,
                    created_at,
                    updated_at
                FROM nasabah
                """
            )
            conn.execute("DROP TABLE nasabah")
            conn.execute("ALTER TABLE nasabah_new RENAME TO nasabah")
        conn.commit()


def fetch_all():
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM nasabah ORDER BY id DESC", conn)


def fetch_one(nasabah_id: int):
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM nasabah WHERE id=?", (int(nasabah_id),))
        row = cur.fetchone()
        return dict(row) if row else None


def create_nasabah(nama, pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan):
    kelayakan, rasio, alasan = tentukan_kelayakan(
        pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan
    )
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO nasabah (
                nama, pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan,
                rasio, kelayakan, alasan, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nama, float(pendapatan), float(jumlah_pinjaman), int(bool(pekerjaan_stabil)), int(skor_slik), int(bool(jaminan)),
                float(rasio), kelayakan, alasan, now, now
            ),
        )
        conn.commit()


def update_nasabah(nasabah_id, nama, pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan):
    kelayakan, rasio, alasan = tentukan_kelayakan(
        pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan
    )
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE nasabah
            SET nama=?, pendapatan=?, jumlah_pinjaman=?, pekerjaan_stabil=?, skor_slik=?, jaminan=?,
                rasio=?, kelayakan=?, alasan=?, updated_at=?
            WHERE id=?
            """,
            (
                nama, float(pendapatan), float(jumlah_pinjaman), int(bool(pekerjaan_stabil)), int(skor_slik), int(bool(jaminan)),
                float(rasio), kelayakan, alasan, now, int(nasabah_id)
            ),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_nasabah(nasabah_id):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM nasabah WHERE id=?", (int(nasabah_id),))
        conn.commit()
        return cur.rowcount > 0


st.set_page_config(page_title="Cek Kelayakan Kredit Nasabah", layout="wide")
init_db()

st.title("Cek Kelayakan Kredit Nasabah")

if "edit_id" not in st.session_state:
    st.session_state["edit_id"] = None
if "del_id" not in st.session_state:
    st.session_state["del_id"] = None
if "confirm_delete_id" not in st.session_state:
    st.session_state["confirm_delete_id"] = None
if "add_form_key" not in st.session_state:
    st.session_state["add_form_key"] = 0

tab_list, tab_add = st.tabs(["Daftar Nasabah", "Tambah Nasabah"])

with tab_list:
    df = fetch_all()

    col1, col2 = st.columns([2, 2])
    with col1:
        q = st.text_input("Cari nama", "")
    with col2:
        fil = st.selectbox("Filter status", ["Semua", "RESIKO", "GOOD", "MODERATE"])

    view = df.copy()
    if not view.empty:
        if q.strip():
            view = view[view["nama"].str.contains(q.strip(), case=False, na=False)]
        if fil != "Semua":
            view = view[view["kelayakan"] == fil]

    if view.empty:
        st.info("Tidak ada data untuk ditampilkan.")
    else:
        st.markdown("**Daftar nasabah**")
        header = st.columns([1, 3, 2, 2, 2, 1, 2, 2, 2, 3, 2])
        header[0].markdown("**ID**")
        header[1].markdown("**Nama**")
        header[2].markdown("**Pendapatan**")
        header[3].markdown("**Pinjaman**")
        header[4].markdown("**Pekerjaan Stabil**")
        header[5].markdown("**Skor SLIK**")
        header[6].markdown("**Jaminan**")
        header[7].markdown("**Status**")
        header[8].markdown("**Rasio**")
        header[9].markdown("**Aksi**")

        for _, row in view.iterrows():
            cols = st.columns([1, 3, 2, 2, 2, 1, 2, 2, 2, 3, 2])
            cols[0].write(int(row["id"]))
            cols[1].write(row["nama"])
            cols[2].write(f'{float(row["pendapatan"]):,.0f}')
            cols[3].write(f'{float(row["jumlah_pinjaman"]):,.0f}')
            cols[4].write("Ya" if normalize_bool(row["pekerjaan_stabil"]) else "Tidak")
            cols[5].write(int(row["skor_slik"]))
            cols[6].write("Ya" if normalize_bool(row["jaminan"]) else "Tidak")
            cols[7].markdown(render_status_badge(row["kelayakan"]), unsafe_allow_html=True)
            cols[8].write(f'{float(row["rasio"]):.2f}')

            aksi = cols[9].columns([1, 1], gap="small")
            if aksi[0].button("Edit", key=f"edit_{int(row['id'])}", use_container_width=True):
                st.session_state["edit_id"] = int(row["id"])
                st.rerun()

            if aksi[1].button("Hapus", key=f"del_{int(row['id'])}", use_container_width=True):
                st.session_state["confirm_delete_id"] = int(row["id"])
                st.rerun()

    if st.session_state["confirm_delete_id"]:
        del_id = int(st.session_state["confirm_delete_id"])
        row = fetch_one(del_id)
        st.warning("Konfirmasi hapus data berikut:")
        if row:
            st.json({"id": row["id"], "nama": row["nama"], "status": row["kelayakan"], "rasio": row["rasio"], "alasan": row["alasan"]})
        else:
            st.info("Data tidak ditemukan.")
        c1, c2 = st.columns([1, 1])
        if c1.button("Ya, hapus", type="primary", key="confirm_del_yes"):
            deleted = delete_nasabah(del_id)
            if deleted:
                st.success(f"ID {del_id} berhasil dihapus.")
            else:
                st.error("Hapus gagal (ID tidak ditemukan).")
            st.session_state["confirm_delete_id"] = None
            st.rerun()
        if c2.button("Batal", key="confirm_del_no"):
            st.session_state["confirm_delete_id"] = None
            st.rerun()

    if st.session_state["edit_id"]:
        st.markdown("---")
        st.subheader("Edit Data")
        edit_id = st.number_input(
            "ID yang akan diedit",
            min_value=1,
            step=1,
            value=int(st.session_state["edit_id"]),
            key="edit_id_input",
        )
        st.session_state["edit_id"] = int(edit_id)
        row = fetch_one(int(edit_id)) if edit_id else None

        if not row:
            st.info("Masukkan ID yang valid (lihat di tabel list).")
        else:
            with st.form("edit_form"):
                nama = st.text_input("Nama", value=row["nama"])
                pendapatan = st.number_input("Pendapatan", min_value=0.0, value=float(row["pendapatan"]), step=100000.0, format="%.0f")
                jumlah_pinjaman = st.number_input("Jumlah pinjaman", min_value=0.0, value=float(row["jumlah_pinjaman"]), step=100000.0, format="%.0f")
                pekerjaan_stabil = st.checkbox("Pekerjaan stabil?", value=normalize_bool(row["pekerjaan_stabil"]))
                skor_slik = st.selectbox("Skor SLIK", [1,2,3,4,5], index=int(row["skor_slik"]) - 1)
                jaminan = st.checkbox("Ada jaminan?", value=normalize_bool(row["jaminan"]))
                ok = st.form_submit_button("Update")

            if ok:
                if not nama.strip():
                    st.error("Nama wajib diisi.")
                elif pendapatan <= 0:
                    st.error("Pendapatan harus > 0.")
                else:
                    updated = update_nasabah(int(edit_id), nama.strip(), pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan)
                    if updated:
                        st.success("Data berhasil diupdate.")
                        st.session_state["edit_id"] = None
                        st.rerun()
                    else:
                        st.error("Update gagal (ID tidak ditemukan).")

with tab_add:
    with st.form(f"add_form_{st.session_state['add_form_key']}"):
        nama = st.text_input("Nama nasabah")
        pendapatan = st.number_input("Pendapatan bulanan", min_value=0.0, step=100000.0, format="%.0f")
        jumlah_pinjaman = st.number_input("Jumlah pinjaman", min_value=0.0, step=100000.0, format="%.0f")
        pekerjaan_stabil = st.checkbox("Pekerjaan stabil?")
        skor_slik = st.selectbox("Skor SLIK", [1, 2, 3, 4, 5])
        jaminan = st.checkbox("Ada jaminan?")
        ok = st.form_submit_button("Simpan")

    if ok:
        if not nama.strip():
            st.error("Nama wajib diisi.")
        elif pendapatan <= 0:
            st.error("Pendapatan harus > 0.")
        else:
            create_nasabah(nama.strip(), pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan)
            st.success("Data tersimpan.")
            st.session_state["add_form_key"] += 1
            st.rerun()
