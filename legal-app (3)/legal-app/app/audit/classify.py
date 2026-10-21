def classify_instrument(a: dict) -> dict:
    """Decision tree pemilihan instrumen."""
    if a["kerja_sama"]:
        inst = "pks" if a["hak_kewajiban_mengikat"] else "mou"
        why = "Kerja sama: mengikat -> PKS, kesepahaman -> MoU."
    elif a["mengatur_norma_umum"]:
        if a["membebani_hak_kewajiban_sanksi_pungutan"]:
            inst, why = "perda", "Norma umum yang membebani/sanksi/pungutan wajib dengan Perda."
        elif a["menjabarkan_peraturan_di_atasnya"]:
            inst, why = "perbup", "Menjabarkan peraturan di atasnya -> Perbup."
        else:
            inst, why = "perda", "Norma umum tanpa perintah delegasi -> kaji sebagai Perda."
    else:
        inst, why = "kepbup", "Penetapan konkret dan individual -> Keputusan Bupati."
    return {"instrument": inst, "alasan": why}
