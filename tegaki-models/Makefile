all=$(allzinnia) $(allwagomu)

allzinnia=tegaki-zinnia-japanese tegaki-zinnia-japanese-light \
tegaki-zinnia-japanese-joyo tegaki-zinnia-japanese-kyoiku \
tegaki-zinnia-simplified-chinese tegaki-zinnia-simplified-chinese-light \
tegaki-zinnia-traditional-chinese tegaki-zinnia-traditional-chinese-light

allwagomu=tegaki-wagomu-japanese \
tegaki-wagomu-japanese-joyo tegaki-wagomu-japanese-kyoiku \
tegaki-wagomu-simplified-chinese

alldist=$(allzinniadist) $(allwagomudist)

allzinniadist=tegaki-zinnia-japanese-dist tegaki-zinnia-japanese-light-dist \
tegaki-zinnia-japanese-joyo-dist tegaki-zinnia-japanese-kyoiku-dist \
tegaki-zinnia-simplified-chinese-dist \
tegaki-zinnia-simplified-chinese-light-dist \
tegaki-zinnia-traditional-chinese-dist \
tegaki-zinnia-traditional-chinese-light-dist

allwagomudist=tegaki-wagomu-japanese-dist \
tegaki-wagomu-japanese-joyo-dist tegaki-wagomu-japanese-kyoiku-dist \
tegaki-wagomu-simplified-chinese-dist

all: $(all)

# model names
tegaki-zinnia-japanese: build/tegaki-zinnia-japanese/handwriting-ja.model
tegaki-zinnia-japanese-light: build/tegaki-zinnia-japanese-light/handwriting-ja.model
tegaki-zinnia-japanese-kyoiku: build/tegaki-zinnia-japanese-kyoiku/kyoiku-kanji.model
tegaki-zinnia-japanese-joyo: build/tegaki-zinnia-japanese-joyo/joyo-kanji.model
tegaki-zinnia-simplified-chinese: build/tegaki-zinnia-simplified-chinese/handwriting-zh_CN.model
tegaki-zinnia-simplified-chinese-light: build/tegaki-zinnia-simplified-chinese-light/handwriting-zh_CN.model
tegaki-zinnia-traditional-chinese: build/tegaki-zinnia-traditional-chinese/handwriting-zh_TW.model
tegaki-zinnia-traditional-chinese-light: build/tegaki-zinnia-traditional-chinese-light/handwriting-zh_TW.model

tegaki-wagomu-japanese: build/tegaki-wagomu-japanese/handwriting-ja.model
tegaki-wagomu-japanese-kyoiku: build/tegaki-wagomu-japanese-kyoiku/kyoiku-kanji.model
tegaki-wagomu-japanese-joyo: build/tegaki-wagomu-japanese-joyo/joyo-kanji.model
tegaki-wagomu-simplified-chinese: build/tegaki-wagomu-simplified-chinese/handwriting-zh_CN.model

# shortcuts
tzj: tegaki-zinnia-japanese
tzjl: tegaki-zinnia-japanese-light
tzjk: tegaki-zinnia-japanese-kyoiku
tzjj: tegaki-zinnia-japanese-joyo
tzsc: tegaki-zinnia-simplified-chinese
tzscl: tegaki-zinnia-simplified-chinese-light
tztc: tegaki-zinnia-traditional-chinese
tztcl: tegaki-zinnia-traditional-chinese-light

twj: tegaki-wagomu-japanese
twjk: tegaki-wagomu-japanese-kyoiku
twjj: tegaki-wagomu-japanese-joyo
twsc: tegaki-wagomu-simplified-chinese

# build japanese
build/tegaki-zinnia-japanese/handwriting-ja.model: data/train/japanese/handwriting-ja.xml
	test -d build/tegaki-zinnia-japanese || make tegaki-zinnia-japanese-build
	cp -u -p data/train/japanese/handwriting-ja.xml build/tegaki-zinnia-japanese/
	make -C build/tegaki-zinnia-japanese

build/tegaki-wagomu-japanese/handwriting-ja.model: data/train/japanese/handwriting-ja.xml
	test -d build/tegaki-wagomu-japanese || make tegaki-wagomu-japanese-build
	cp -u -p data/train/japanese/handwriting-ja.xml build/tegaki-wagomu-japanese/
	make -C build/tegaki-wagomu-japanese

build/tegaki-zinnia-japanese-kyoiku/kyoiku-kanji.model: data/train/japanese/handwriting-ja.xml
	test -d build/tegaki-zinnia-japanese-kyoiku || make tegaki-zinnia-japanese-kyoiku-build
	tegaki-convert -t data/train/japanese/handwriting-ja.xml --include data/script/kyoiku-kanji.txt build/tegaki-zinnia-japanese-kyoiku/kyoiku-kanji.xml
	touch -r data/train/japanese/handwriting-ja.xml build/tegaki-zinnia-japanese-kyoiku/kyoiku-kanji.xml
	make -C build/tegaki-zinnia-japanese-kyoiku

build/tegaki-wagomu-japanese-kyoiku/kyoiku-kanji.model: data/train/japanese/handwriting-ja.xml
	test -d build/tegaki-wagomu-japanese-kyoiku || make tegaki-wagomu-japanese-kyoiku-build
	tegaki-convert -t data/train/japanese/handwriting-ja.xml --include data/script/kyoiku-kanji.txt build/tegaki-wagomu-japanese-kyoiku/kyoiku-kanji.xml
	touch -r data/train/japanese/handwriting-ja.xml build/tegaki-wagomu-japanese-kyoiku/kyoiku-kanji.xml
	make -C build/tegaki-wagomu-japanese-kyoiku

build/tegaki-zinnia-japanese-joyo/joyo-kanji.model: data/train/japanese/handwriting-ja.xml
	test -d build/tegaki-zinnia-japanese-joyo || make tegaki-zinnia-japanese-joyo-build
	tegaki-convert -t data/train/japanese/handwriting-ja.xml --include data/script/joyo-kanji.txt build/tegaki-zinnia-japanese-joyo/joyo-kanji.xml
	touch -r data/train/japanese/handwriting-ja.xml build/tegaki-zinnia-japanese-joyo/joyo-kanji.xml
	make -C build/tegaki-zinnia-japanese-joyo

build/tegaki-wagomu-japanese-joyo/joyo-kanji.model: data/train/japanese/handwriting-ja.xml
	test -d build/tegaki-wagomu-japanese-joyo || make tegaki-wagomu-japanese-joyo-build
	tegaki-convert -t data/train/japanese/handwriting-ja.xml --include data/script/joyo-kanji.txt build/tegaki-wagomu-japanese-joyo/joyo-kanji.xml
	touch -r data/train/japanese/handwriting-ja.xml build/tegaki-wagomu-japanese-joyo/joyo-kanji.xml
	make -C build/tegaki-wagomu-japanese-joyo

# build simplified-chinese
build/tegaki-zinnia-simplified-chinese/handwriting-zh_CN.model: data/train/simplified-chinese/handwriting-zh_CN.xml
	test -d build/tegaki-zinnia-simplified-chinese || make tegaki-zinnia-simplified-chinese-build
	cp -u -p data/train/simplified-chinese/handwriting-zh_CN.xml build/tegaki-zinnia-simplified-chinese
	make -C build/tegaki-zinnia-simplified-chinese

build/tegaki-wagomu-simplified-chinese/handwriting-zh_CN.model: data/train/simplified-chinese/handwriting-zh_CN.xml
	test -d build/tegaki-wagomu-simplified-chinese || make tegaki-wagomu-simplified-chinese-build
	cp -u -p data/train/simplified-chinese/handwriting-zh_CN.xml build/tegaki-wagomu-simplified-chinese
	make -C build/tegaki-wagomu-simplified-chinese

# build traditional chinese
build/tegaki-zinnia-traditional-chinese/handwriting-zh_TW.model: data/train/traditional-chinese/handwriting-zh_TW.xml data/train/traditional-chinese/out-domain data/train/simplified-chinese/handwriting-zh_CN.xml data/train/japanese/handwriting-ja.xml
	test -d build/tegaki-zinnia-traditional-chinese || make tegaki-zinnia-traditional-chinese-build
	tegaki-bootstrap -q --domain=BIG5 --locale=T --max-samples=1 \
build/tegaki-zinnia-traditional-chinese/handwriting-zh_TW.xml \
-c data/train/traditional-chinese/handwriting-zh_TW.xml \
-d data/train/traditional-chinese/out-domain \
-t data/train/simplified-chinese/handwriting-zh_CN.xml \
-t data/train/japanese/handwriting-ja.xml
	make -C build/tegaki-zinnia-traditional-chinese

# light models
build/tegaki-zinnia-japanese-light/handwriting-ja.model: tegaki-zinnia-japanese
	rm -rf build/tegaki-zinnia-japanese-light
	cp -R -p build/tegaki-zinnia-japanese build/tegaki-zinnia-japanese-light
	zinnia_convert -c 0.005 build/tegaki-zinnia-japanese-light/handwriting-ja.model.txt \
build/tegaki-zinnia-japanese-light/handwriting-ja.model

build/tegaki-zinnia-simplified-chinese-light/handwriting-zh_CN.model: tegaki-zinnia-simplified-chinese
	rm -rf build/tegaki-zinnia-simplified-chinese-light
	cp -R -p build/tegaki-zinnia-simplified-chinese build/tegaki-zinnia-simplified-chinese-light
	zinnia_convert -c 0.005 build/tegaki-zinnia-simplified-chinese-light/handwriting-zh_CN.model.txt \
build/tegaki-zinnia-simplified-chinese-light/handwriting-zh_CN.model

build/tegaki-zinnia-traditional-chinese-light/handwriting-zh_TW.model: tegaki-zinnia-traditional-chinese
	rm -rf build/tegaki-zinnia-traditional-chinese-light
	cp -R -p build/tegaki-zinnia-traditional-chinese build/tegaki-zinnia-traditional-chinese-light
	zinnia_convert -c 0.005 build/tegaki-zinnia-traditional-chinese-light/handwriting-zh_TW.model.txt \
build/tegaki-zinnia-traditional-chinese-light/handwriting-zh_TW.model

# prepare build-directory
tegaki-zinnia-japanese-build tegaki-zinnia-japanese-joyo-build tegaki-zinnia-japanese-kyoiku-build tegaki-zinnia-simplified-chinese-build tegaki-zinnia-traditional-chinese-build:
	model=$(subst -build,,$@); \
	mkdir -p build/$$model; \
	cp $$model/* build/$$model/; \
	sed "s?\[recognizer-name\]?zinnia?" < README.in > build/$$model/README.txt; \
	cp LGPL build/$$model/COPYING

tegaki-wagomu-japanese-build tegaki-wagomu-japanese-joyo-build tegaki-wagomu-japanese-kyoiku-build tegaki-wagomu-simplified-chinese-build:
	model=$(subst -build,,$@); \
	mkdir -p build/$$model; \
	cp $$model/* build/$$model/; \
	sed "s?\[recognizer-name\]?wagomu?" < README.in > build/$$model/README.txt; \
	cp LGPL build/$$model/COPYING

# prepare all zip files
dist: $(alldist)

$(alldist): $(all)
	model=$(subst -dist,,$@); \
	version=`cat build/$$model/VERSION`; \
	mkdir -p dist; \
	rm -rf dist/$$model; \
	cp -R build/$$model dist/$$model-$$version; \
	rm dist/*/*.model.txt ; \
	(cd dist/; rm $$model-$$version.zip; zip -r $$model-$$version.zip $$model-$$version) ; \
	rm -rf dist/$$model-$$version

# force to rebuild next time!
clean:
	rm -rf build/*
