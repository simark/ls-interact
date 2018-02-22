namespace ns1 {
  template <typename Taloche>
  void foo(int x = 0,
	   int y = 0)
  {
    Taloche t;
  }
}

int main(int argc, char **argv) {
  ns1::foo<int>();
  return 0;
}
