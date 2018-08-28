(TeX-add-style-hook
 "design_document"
 (lambda ()
   (setq TeX-command-extra-options
         "-shell-escape")
   (TeX-add-to-alist 'LaTeX-provided-class-options
                     '(("ctexart" "11pt")))
   (TeX-add-to-alist 'LaTeX-provided-package-options
                     '(("ulem" "normalem")))
   (add-to-list 'LaTeX-verbatim-environments-local "lstlisting")
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "path")
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "url")
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "nolinkurl")
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "hyperbaseurl")
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "hyperimage")
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "hyperref")
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "lstinline")
   (add-to-list 'LaTeX-verbatim-macros-with-delims-local "path")
   (add-to-list 'LaTeX-verbatim-macros-with-delims-local "lstinline")
   (TeX-run-style-hooks
    "latex2e"
    "ctexart"
    "ctexart11"
    "graphicx"
    "grffile"
    "longtable"
    "wrapfig"
    "rotating"
    "ulem"
    "amsmath"
    "textcomp"
    "amssymb"
    "capt-of"
    "hyperref"
    "xeCJK"
    "xcolor"
    "listings")
   (TeX-add-symbols
    "baselinestretch")
   (LaTeX-add-labels
    "sec:orgb5d7302"
    "sec:orgc389e4f"
    "sec:orgc5a034f"
    "sec:orge68b49b"
    "sec:orgac49d5c"
    "sec:org8e37e5d"
    "sec:org7062a3d"
    "sec:org465d866"
    "sec:orge8d01d8"
    "sec:orgfda7246"
    "sec:org9262928"
    "sec:org399148e"
    "sec:org7b5301f"
    "sec:org5a0d209"))
 :latex)

