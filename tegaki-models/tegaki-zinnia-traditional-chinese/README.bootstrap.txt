Bootstrapping
=============

This handwriting model is bootstrapped using other existing models. This process
helps to quickly create a large model, using data of characters' components.
This comes at a cost of potentially ill fitting models, as other sources might
employ different stroke order or other particular writing styles. Auto-generated
models can be easily overwritten by supplying a manual data set within the
source file.

Building
--------
This archive contains a pre-built .xml file but if you like, you can
re-run the bootstrapping process from source using "tegaki-bootstrap", available
from tegaki-tools. This requires external dependency cjklib
(http://code.google.com/p/cjklib).

$ tegaki-bootstrap -q --domain=BIG5 --locale=T --max-samples=1 \
    handwriting-zh_TW.xml \
    -c ../data/train/traditional-chinese/handwriting-zh_TW.xml \
    -d ../data/train/traditional-chinese/out-domain \
    -t ../data/train/simplified-chinese/handwriting-zh_CN.xml \
    -t ../data/train/japanese/handwriting-ja.xml

To build the final model file, please see README.txt.

$ tegaki-build -c handwriting-zh_TW.xml zinnia handwriting-zh_TW.meta

Evalutation
-----------
To evaluate the bootstrapped model against some test data, run:

$ tegaki-eval -d ../data/test/traditional-chinese/ zinnia "Traditional Chinese"
