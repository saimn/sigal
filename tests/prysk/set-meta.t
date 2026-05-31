Check set-meta command:

  $ mkdir pictures
  $ touch pictures/test.jpg
  $ sigal set-meta pictures title "My Gallery"
  1 metadata key(s) written to *index.md (glob)
  $ cat pictures/index.md
  Title: My Gallery

  $ sigal set-meta pictures/test.jpg title "My Image"
  1 metadata key(s) written to *test.md (glob)
  $ cat pictures/test.md
  Title: My Image

Check error on odd number of arguments:
  $ sigal set-meta pictures title
  Need an even number of arguments.
  [1]
