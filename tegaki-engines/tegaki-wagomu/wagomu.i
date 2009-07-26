%module wagomu
%{
#include "wagomu.h"
%}

%include "carrays.i"
%array_class(float, FloatArray);

%newobject recognize;

%include "wagomu.h"