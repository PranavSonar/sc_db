rm -rf ~/candles_NSEEQ_2
python scripts/scan_security_list_technical.py --invs scripts/db/investing_dot_com_security_dict.py --lag 60 --res 1W --sfile scripts/db/nse_all_eq.csv --plots_dir ~/candles_NSEEQ_2 --plot_mon
