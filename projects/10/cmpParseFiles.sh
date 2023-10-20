#!/usr/bin/env

# ArrayTest
FOLDER=ArrayTest
python JackAnalyzer.py ${FOLDER}
echo "Comparing ${FOLDER}/Main.xml"
../../tools/TextComparer.sh ${FOLDER}/Main.xml ${FOLDER}/cmp/Main.xml

# ExpressionLessSquare
FOLDER=ExpressionLessSquare
python JackAnalyzer.py ${FOLDER}
echo "Comparing ${FOLDER}/Square.xml"
../../tools/TextComparer.sh ${FOLDER}/Square.xml ${FOLDER}/cmp/Square.xml
echo "Comparing ${FOLDER}/SquareGame.xml"
../../tools/TextComparer.sh ${FOLDER}/SquareGame.xml ${FOLDER}/cmp/SquareGame.xml
echo "Comparing ${FOLDER}/Main.xml"
../../tools/TextComparer.sh ${FOLDER}/Main.xml ${FOLDER}/cmp/Main.xml

# Square
FOLDER=Square
python JackAnalyzer.py ${FOLDER}
echo "Comparing ${FOLDER}/Square.xml"
../../tools/TextComparer.sh ${FOLDER}/Square.xml ${FOLDER}/cmp/Square.xml
echo "Comparing ${FOLDER}/SquareGame.xml"
../../tools/TextComparer.sh ${FOLDER}/SquareGame.xml ${FOLDER}/cmp/SquareGame.xml
echo "Comparing ${FOLDER}/Main.xml"
../../tools/TextComparer.sh ${FOLDER}/Main.xml ${FOLDER}/cmp/Main.xml
