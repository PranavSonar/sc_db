rm -rf ~/candles_bse_group_B_1D
python scripts/scan_security_list_technical.py --invs scripts/db/investing_dot_com_security_dict.py --ma_plist '9,14' --lag 60 --res 1D --sfile scripts/db/bse_group_B.csv --plots_dir ~/candles_bse_group_B_1D
