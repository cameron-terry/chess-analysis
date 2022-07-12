echo '=================='
echo ' data_analysis.sh '
echo '=================='

echo 'Querying Chess.com, Updating database...'
python update_db.py

echo 'Calculating heuristics...'
python heuristics.py

echo 'Updating chess_stock...'
python chess_stock.py

echo 'Done!'