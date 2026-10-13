Check export-epub command:

  $ mkdir pictures
  $ cp "$TESTDIR/../sample/pictures/dir2/KeckObservatory20071020.jpg" pictures/
  $ sigal init > /dev/null
  $ sigal export-epub pictures -o album.epub > /dev/null 2>&1
  $ ls album.epub
  album.epub
