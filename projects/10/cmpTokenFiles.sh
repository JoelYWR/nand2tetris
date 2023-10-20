#!/usr/bin/env

# ArrayTest
FOLDER=ArrayTest
python JackAnalyzer.py ${FOLDER} -m t
echo "Comparing ${FOLDER}/MainT.xml"
../../tools/TextComparer.sh ${FOLDER}/MainT.xml ${FOLDER}/cmp/MainT.xml

# ExpressionLessSquare
FOLDER=ExpressionLessSquare
python JackAnalyzer.py ${FOLDER} -m t
echo "Comparing ${FOLDER}/SquareT.xml"
../../tools/TextComparer.sh ${FOLDER}/SquareT.xml ${FOLDER}/cmp/SquareT.xml
echo "Comparing ${FOLDER}/SquareGameT.xml"
../../tools/TextComparer.sh ${FOLDER}/SquareGameT.xml ${FOLDER}/cmp/SquareGameT.xml
echo "Comparing ${FOLDER}/MainT.xml"
../../tools/TextComparer.sh ${FOLDER}/MainT.xml ${FOLDER}/cmp/MainT.xml

# Square
FOLDER=Square
python JackAnalyzer.py ${FOLDER} -m t
echo "Comparing ${FOLDER}/SquareT.xml"
../../tools/TextComparer.sh ${FOLDER}/SquareT.xml ${FOLDER}/cmp/SquareT.xml
echo "Comparing ${FOLDER}/SquareGameT.xml"
../../tools/TextComparer.sh ${FOLDER}/SquareGameT.xml ${FOLDER}/cmp/SquareGameT.xml
echo "Comparing ${FOLDER}/MainT.xml"
../../tools/TextComparer.sh ${FOLDER}/MainT.xml ${FOLDER}/cmp/MainT.xml
