#include "first.h"
#include "second.h"

#if BUILD == 1
#warning "This is build 1"
#elif BUILD == 2
#warning "This is build 2"
#endif


static void foo()
{
  bob();
}

int main()
{
  bar();
  foo();
}
