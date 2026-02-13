import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

DB_PATH = "kredit.db"


# -----------------------------
# Rules
# -----------------------------
@dataclass(frozen=True)
class KelayakanResult:
    status: str
    rasio: float | None
    alasan: str


def tentukan_kelayakan(
    pendapatan: float,
    jumlah_pinjaman: float,
    pekerjaan_stabil: bool,
    skor_slik: int,
    jaminan: bool,
) -> KelayakanResult:
    if pendapatan <= 0:
        return KelayakanResult("RESIKO", None, "Pendapatan tidak valid")

    if not (1 <= skor_slik <= 5):
        return KelayakanResult("RESIKO", None, "Skor SLIK harus antara 1-5")

    rasio = (jumlah_pinjaman or 0) / pendapatan

    if skor_slik >= 4:
        return KelayakanResult("RESIKO", rasio, "SLIK macet / buruk")

    if rasio >= 0.5:
        return KelayakanResult("RESIKO", rasio, "Jumlah pinjaman terlalu besar dibanding pendapatan")

    if rasio <= 0.2 and skor_slik <= 2 and (pekerjaan_stabil or jaminan):
        return KelayakanResult("GOOD", rasio, "Risiko rendah")

    if (0.2 < rasio <= 0.5) and skor_slik <= 3 and (pekerjaan_stabil or jaminan):
        return KelayakanResult("MODERATE", rasio, "Risiko sedang")

    if rasio <= 0.15 and skor_slik <= 2:
        return KelayakanResult("MODERATE", rasio, "Pendapatan tidak stabil tapi rasio dan SLIK baik")

    return KelayakanResult("RESIKO", rasio, "Risiko tinggi")



def utc_now_str() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def normalize_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"ya", "1", "true", "yes", "y"}
    return bool(int(value)) if isinstance(value, (int, float)) else bool(value)


def status_badge_html(status: str) -> str:
    palette = {
        "GOOD": ("#1b5e20", "#c8e6c9"),
        "MODERATE": ("#f57f17", "#fff9c4"),
        "RESIKO": ("#b71c1c", "#ffcdd2"),
    }
    color, bg = palette.get(status, ("#616161", "#eeeeee"))
    return (
        f"<span style='font-weight:600;color:{color};background:{bg};"
        "padding:2px 8px;border-radius:12px;display:inline-block'>"
        f"{status}</span>"
    )



@st.cache_resource
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
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
    col_types = {row["name"]: (row["type"] or "").upper() for row in info}
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
                id, nama, pendapatan, jumlah_pinjaman,
                pekerjaan_stabil, skor_slik, jaminan,
                rasio, kelayakan, alasan, created_at, updated_at
            )
            SELECT
                id,
                nama,
                pendapatan,
                jumlah_pinjaman,
                CASE WHEN pekerjaan_stabil IN ('ya','YA','1','true','TRUE','yes','YES') THEN 1 ELSE 0 END,
                skor_slik,
                CASE WHEN jaminan IN ('ya','YA','1','true','TRUE','yes','YES') THEN 1 ELSE 0 END,
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


def fetch_all() -> pd.DataFrame:
    conn = get_conn()
    return pd.read_sql_query("SELECT * FROM nasabah ORDER BY id DESC", conn)


def fetch_one(nasabah_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM nasabah WHERE id=?", (int(nasabah_id),)).fetchone()
    return dict(row) if row else None


def create_nasabah(
    nama: str,
    pendapatan: float,
    jumlah_pinjaman: float,
    pekerjaan_stabil: bool,
    skor_slik: int,
    jaminan: bool,
) -> None:
    res = tentukan_kelayakan(pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan)
    now = utc_now_str()
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO nasabah (
            nama, pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan,
            rasio, kelayakan, alasan, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nama.strip(),
            float(pendapatan),
            float(jumlah_pinjaman),
            int(bool(pekerjaan_stabil)),
            int(skor_slik),
            int(bool(jaminan)),
            float(res.rasio or 0),
            res.status,
            res.alasan,
            now,
            now,
        ),
    )
    conn.commit()


def update_nasabah(
    nasabah_id: int,
    nama: str,
    pendapatan: float,
    jumlah_pinjaman: float,
    pekerjaan_stabil: bool,
    skor_slik: int,
    jaminan: bool,
) -> bool:
    res = tentukan_kelayakan(pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan)
    now = utc_now_str()
    conn = get_conn()
    cur = conn.execute(
        """
        UPDATE nasabah
        SET nama=?, pendapatan=?, jumlah_pinjaman=?,
            pekerjaan_stabil=?, skor_slik=?, jaminan=?,
            rasio=?, kelayakan=?, alasan=?, updated_at=?
        WHERE id=?
        """,
        (
            nama.strip(),
            float(pendapatan),
            float(jumlah_pinjaman),
            int(bool(pekerjaan_stabil)),
            int(skor_slik),
            int(bool(jaminan)),
            float(res.rasio or 0),
            res.status,
            res.alasan,
            now,
            int(nasabah_id),
        ),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_nasabah(nasabah_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM nasabah WHERE id=?", (int(nasabah_id),))
    conn.commit()
    return cur.rowcount > 0



st.set_page_config(page_title="Cek Kelayakan Kredit Nasabah", layout="wide")
init_db()

st.title("Cek Kelayakan Kredit Nasabah")

st.session_state.setdefault("edit_id", None)
st.session_state.setdefault("confirm_delete_id", None)
st.session_state.setdefault("add_form_key", 0)

tab_list, tab_add = st.tabs(["Daftar Nasabah", "Tambah Nasabah"])

with tab_list:
    df = fetch_all()

    c1, c2 = st.columns([2, 2])
    with c1:
        q = st.text_input("Cari nama", "")
    with c2:
        fil = st.selectbox("Filter status", ["Semua", "RESIKO", "GOOD", "MODERATE"])

    view = df
    if not view.empty:
        if q.strip():
            view = view[view["nama"].str.contains(q.strip(), case=False, na=False)]
        if fil != "Semua":
            view = view[view["kelayakan"] == fil]

    if view.empty:
        st.info("Tidak ada data untuk ditampilkan.")
    else:
        st.markdown("**Daftar nasabah**")
        header = st.columns([1, 3, 2, 2, 2, 1, 2, 2, 2, 3])
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
            cols = st.columns([1, 3, 2, 2, 2, 1, 2, 2, 2, 3])

            nid = int(row["id"])
            cols[0].write(nid)
            cols[1].write(row["nama"])
            cols[2].write(f"{float(row['pendapatan']):,.0f}")
            cols[3].write(f"{float(row['jumlah_pinjaman']):,.0f}")
            cols[4].write("Ya" if normalize_bool(row["pekerjaan_stabil"]) else "Tidak")
            cols[5].write(int(row["skor_slik"]))
            cols[6].write("Ya" if normalize_bool(row["jaminan"]) else "Tidak")
            cols[7].markdown(status_badge_html(row["kelayakan"]), unsafe_allow_html=True)
            cols[8].write(f"{float(row['rasio']):.2f}")

            aksi = cols[9].columns([1, 1], gap="small")
            if aksi[0].button("Edit", key=f"edit_{nid}", use_container_width=True):
                st.session_state["edit_id"] = nid
                st.rerun()

            if aksi[1].button("Hapus", key=f"del_{nid}", use_container_width=True):
                st.session_state["confirm_delete_id"] = nid
                st.rerun()

    # Delete confirmation
    if st.session_state["confirm_delete_id"]:
        del_id = int(st.session_state["confirm_delete_id"])
        row = fetch_one(del_id)

        st.warning("Konfirmasi hapus data berikut:")
        if row:
            st.json(
                {
                    "id": row["id"],
                    "nama": row["nama"],
                    "status": row["kelayakan"],
                    "rasio": row["rasio"],
                    "alasan": row["alasan"],
                }
            )
        else:
            st.info("Data tidak ditemukan.")

        b1, b2 = st.columns(2)
        if b1.button("Ya, hapus", type="primary", key="confirm_del_yes"):
            if delete_nasabah(del_id):
                st.success(f"ID {del_id} berhasil dihapus.")
            else:
                st.error("Hapus gagal (ID tidak ditemukan).")
            st.session_state["confirm_delete_id"] = None
            st.rerun()

        if b2.button("Batal", key="confirm_del_no"):
            st.session_state["confirm_delete_id"] = None
            st.rerun()

    # Edit form
    if st.session_state["edit_id"]:
        st.markdown("---")
        st.subheader("Edit Data")

        edit_id = st.number_input(
            "ID yang akan diedit",
            min_value=1,
            step=1,
            value=int(st.session_state["edit_id"]),
        )
        st.session_state["edit_id"] = int(edit_id)

        row = fetch_one(int(edit_id))
        if not row:
            st.info("Masukkan ID yang valid (lihat di tabel list).")
        else:
            with st.form("edit_form"):
                nama = st.text_input("Nama", value=row["nama"])
                pendapatan = st.number_input(
                    "Pendapatan",
                    min_value=0.0,
                    value=float(row["pendapatan"]),
                    step=100000.0,
                    format="%.0f",
                )
                jumlah_pinjaman = st.number_input(
                    "Jumlah pinjaman",
                    min_value=0.0,
                    value=float(row["jumlah_pinjaman"]),
                    step=100000.0,
                    format="%.0f",
                )
                pekerjaan_stabil = st.checkbox(
                    "Pekerjaan stabil?",
                    value=normalize_bool(row["pekerjaan_stabil"]),
                )
                skor_slik = st.selectbox("Skor SLIK", [1, 2, 3, 4, 5], index=int(row["skor_slik"]) - 1)
                jaminan = st.checkbox("Ada jaminan?", value=normalize_bool(row["jaminan"]))
                ok = st.form_submit_button("Update")

            if ok:
                if not nama.strip():
                    st.error("Nama wajib diisi.")
                elif pendapatan <= 0:
                    st.error("Pendapatan harus > 0.")
                else:
                    if update_nasabah(
                        int(edit_id),
                        nama,
                        pendapatan,
                        jumlah_pinjaman,
                        pekerjaan_stabil,
                        skor_slik,
                        jaminan,
                    ):
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
            create_nasabah(nama, pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan)
            st.success("Data tersimpan.")
            st.session_state["add_form_key"] += 1
            st.rerun()
