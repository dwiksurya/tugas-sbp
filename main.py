from tabulate import tabulate
from datetime import datetime

nasabah_list = []
auto_id_increment = 1

def input_float(value):
    while True:
        try:
            return float(input(value))
        except:
            print("Input harus angka")


def input_int_range(value, min_val, max_val):
    while True:
        try:
            val = int(input(value))
            if min_val <= val <= max_val:
                return val
            print(f"Input harus antara {min_val}-{max_val}")
        except:
            print("Input harus angka bulat")


def input_yesno(value):
    while True:
        val = input(value).lower()
        if val in ["y", "n"]:
            return val == "y"
        print("Input harus y/n")


# RULES        
def tentukan_kelayakan(
    pendapatan,
    jumlah_pinjaman,
    pekerjaan_stabil,
    skor_slik,
    jaminan
):
    if pendapatan <= 0:
        return "RESIKO", None, "Pendapatan tidak valid"

    if skor_slik < 1 or skor_slik > 5:
        return "RESIKO", None, "Skor SLIK harus antara 1-5"

    rasio = jumlah_pinjaman / pendapatan

    if skor_slik >= 4:
        return "RESIKO", rasio, "SLIK macet / buruk"

    if rasio >= 5:
        return "RESIKO", rasio, "Jumlah pinjaman terlalu besar dibanding pendapatan"

    if (
        rasio <= 2 and
        skor_slik <= 2 and
        (pekerjaan_stabil or jaminan)
    ):
        return "GOOD", rasio, "Risiko rendah"

    if (
        2 < rasio <= 3 and
        skor_slik <= 3 and
        (pekerjaan_stabil or jaminan)
    ):
        return "MODERATE", rasio, "Risiko sedang"

    if (
        rasio <= 1.5 and
        skor_slik <= 2
    ):
        return "MODERATE", rasio, "Pendapatan tidak stabil tapi rasio dan SLIK baik"

    return "RESIKO", rasio, "Risiko tinggi"


def tambah_nasabah():
    global auto_id_increment

    nama = input("Nama: ")
    pendapatan = input_float("Pendapatan: ")
    pinjaman = input_float("Jumlah Pinjaman: ")
    pekerjaan = input_yesno("Pekerjaan stabil/tetap? (y/n): ")
    skor = input_int_range("Skor SLIK (1-5): ", 1, 5)
    jaminan = input_yesno("Ada jaminan? (y/n): ")

    kelayakan, rasio, alasan = tentukan_kelayakan(
        pendapatan, pinjaman, pekerjaan, skor, jaminan
    )

    data = {
        "id": auto_id_increment,
        "nama": nama,
        "pendapatan": pendapatan,
        "pinjaman": pinjaman,
        "pekerjaan_stabil": pekerjaan,
        "skor_slik": skor,
        "jaminan": jaminan,
        "rasio": round(rasio, 2),
        "kelayakan": kelayakan,
        "alasan": alasan,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    nasabah_list.append(data)
    auto_id_increment += 1

    print("Data nasabah berhasil ditambahkan")


def lihat_nasabah():
    if not nasabah_list:
        print("Belum ada data")
        return

    table = []
    for n in nasabah_list:
        table.append([
            n["id"],
            n["nama"],
            n["pendapatan"],
            n["pinjaman"],
            "Ya" if n["pekerjaan_stabil"] else "Tidak",
            n["skor_slik"],
            "Ya" if n["jaminan"] else "Tidak",
            n["rasio"],
            n["kelayakan"],
            n["alasan"]
        ])

    headers = ["ID", "Nama", "Pendapatan", "Pinjaman", "Pekerjaan Stabil/Tetap", "SLIK", "Ada Jaminan", "Rasio", "Status", "Alasan"]
    print(tabulate(table, headers=headers, tablefmt="grid"))


def edit_nasabah():
    idn = int(input("Masukkan ID: "))

    for n in nasabah_list:
        if n["id"] == idn:
            nama = input(f"Nama ({n['nama']}): ") or n["nama"]
            pendapatan = float(input(f"Pendapatan ({n['pendapatan']}): ") or n["pendapatan"])
            pinjaman = float(input(f"Pinjaman ({n['pinjaman']}): ") or n["pinjaman"])
            pekerjaan = input("Pekerjaan stabil/tetap? (y/n): ").lower() == "y"
            skor = int(input(f"Skor SLIK ({n['skor_slik']}): ") or n["skor_slik"])
            jaminan = input("Ada jaminan? (y/n): ").lower() == "y"

            kelayakan, rasio, alasan = tentukan_kelayakan(
                pendapatan, pinjaman, pekerjaan, skor, jaminan
            )

            n.update({
                "nama": nama,
                "pendapatan": pendapatan,
                "pinjaman": pinjaman,
                "pekerjaan_stabil": pekerjaan,
                "skor_slik": skor,
                "jaminan": jaminan,
                "rasio": round(rasio, 2),
                "kelayakan": kelayakan,
                "alasan": alasan
            })

            print("Data berhasil diupdate")
            return

    print("ID tidak ditemukan")


def hapus_nasabah():
    idn = int(input("Masukkan ID yang akan dihapus: "))

    for i, n in enumerate(nasabah_list):
        if n["id"] == idn:
            nasabah_list.pop(i)
            print("🗑 Data berhasil dihapus")
            return

    print("ID tidak ditemukan")


def menu():
    print("\nMENU CEK KELAYAKAN KREDIT NASABAH")
    print("1. Tambah Nasabah")
    print("2. Lihat Nasabah")
    print("3. Edit Nasabah")
    print("4. Hapus Nasabah")
    print("0. Keluar")


def main():
    while True:
        menu()
        pilih = input("Pilih menu: ")

        if pilih == "1":
            tambah_nasabah()
        elif pilih == "2":
            lihat_nasabah()
        elif pilih == "3":
            edit_nasabah()
        elif pilih == "4":
            hapus_nasabah()
        elif pilih == "0":
            print("Program ditutup")
            break
        else:
            print("Menu tidak valid")


if __name__ == "__main__":
    main()
