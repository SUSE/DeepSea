

all: rpm

rpm: tarball
	rpmbuild -bb deepsea.spec

tarball: tests
	VERSION=`awk '/^Version/ {print $$2}' deepsea.spec`; \
	git archive --prefix deepsea/ -o ~/rpmbuild/SOURCES/deepsea-$$VERSION.tar.gz HEAD

tests:
	@echo "Need to write tests :)"

