echo '=================='
echo ' data_analysis.sh '
echo '=================='

echo 'Removing old dataset file, creating new one from new files\n'
rm -f datasets/roudiere.pgn
cat datasets/roudiere-white.pgn datasets/roudiere-black.pgn > datasets/roudiere.pgn

echo 'Updating database...'
python update_db.py

echo 'Calculating heuristics...'
python heuristics.py

echo 'Updating chess_stock...'
python chess_stock.py

echo 'Done!'