#!perl

while(<>) {
  if (m/ledindex...(\d+)\,/) {
    print if $1 % 2 == 0;
  }
  else 
  {
    print;
  }
}
   
