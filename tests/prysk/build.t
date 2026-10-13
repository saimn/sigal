Build a simple gallery:

  $ mkdir pictures
  $ cp "$TESTDIR/../sample/pictures/dir2/KeckObservatory20071020.jpg" pictures/
  $ sigal init > /dev/null
  $ sigal build pictures out --quiet
  
  $ ls out/thumbnails/KeckObservatory20071020.jpg
  out/thumbnails/KeckObservatory20071020.jpg
  $ ls out/index.html
  out/index.html
