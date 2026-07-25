% Plantilla para la memoria del TFG
% Plantilla desarrollada por Juan Gutiérrez Aguado (www.uv.es/jgutierr)
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{tfg}[2020/03/26 Plantilla para la memoria del TFG]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{book}}
\ProcessOptions
\LoadClass{book}

\newcommand{\@tutorlabel}{\ClassError{tfg}{Falta especificar
    \string\tutorlabel{}}
  {Usa el comando \string\tutorlabel{} en el preambulo para especificar
    \MessageBreak la etiqueta asociada (Tutor, Tutora, Tutores)}}
\newcommand{\tutorlabel}[1]{\gdef\@tutorlabel{#1}}

\newcommand{\@authorlabel}{\ClassError{tfg}{Falta especificar
    \string\autorlabel{}}
  {Usa el comando \string\authorlabel{} en el preambulo para especificar
    \MessageBreak la etiqueta asociada (Autor, Autora)}}
\newcommand{\authorlabel}[1]{\gdef\@authorlabel{#1}}

\newcommand{\@tutor}{\ClassError{tfg}{Falta especificar
    \string\tutor{}}
  {Usa el comando \string\tutor{} en el preambulo para especificar
    \MessageBreak el nombre del tutor o la tutora.}}
\newcommand{\tutor}[1]{\gdef\@tutor{#1}}

\newcommand{\@convocatoria}{\ClassError{tfg}{Falta especificar
    \string\convocatoria{}}
  {Usa el comando \string\convocatoria{} en el preambulo para especificar
    \MessageBreak el mes y año de la lectura.}}
\newcommand{\convocatoria}[1]{\gdef\@convocatoria{#1}}


\newcommand{\@titulacion}{\ClassError{tfg}{Falta especificar
    \string\titulación{}}
  {Usa el comando \string\titulacion{} en el preambulo para especificar
    \MessageBreak la titulacion.}}
\newcommand{\titulacion}[1]{\gdef\@titulacion{#1}}


\RequirePackage[T1]{fontenc}
\RequirePackage[spanish,activeacute]{babel}
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{fancyhdr}
\RequirePackage{listings}
\RequirePackage{hyperref}
\RequirePackage[pdftex]{graphicx}
\RequirePackage{tikz}
\RequirePackage{framed}
\RequirePackage{geometry}
\RequirePackage{soul}
\RequirePackage{bold-extra}
\RequirePackage{ragged2e}
\RequirePackage{doi}
\RequirePackage{adjustbox}
\RequirePackage{longtable}
\RequirePackage{eurosym} % Símbolo de euro
\RequirePackage{upquote}
\RequirePackage{caption}
\RequirePackage{subcaption}
\RequirePackage{soul}
\RequirePackage{tabularx}
\RequirePackage{colortbl}
\RequirePackage{rotating}
\RequirePackage{slashbox}
\RequirePackage{fontawesome5}
\RequirePackage{hvlogos}
%\RequirePackage{listing}

\usepackage[newfloat,cache=false]{minted}
\setminted{autogobble,linenos,bgcolor=lightgray,fontsize=\scriptsize,frame=leftline,framesep=2mm,breaklines,breaksymbolleft=,numbersep=3pt}

\usepackage[
  backend=biber, % Use the biber engine for compiling the bibliography
  bibstyle=numeric, % Main bibliography style
  citestyle=numeric, % In-text citation style
  sorting=none, % Sort references as they are cited
  sortcites=true, % If multiple citekeys are passed to a citation command, sort them in the citation
  abbreviate=false, % Suppress abbreviations such as "Ed." for Editor
  backref=true, % List the page where references were cited in the bibliography
  defernumbers=true,
  style=ieee,
  maxbibnames=99,
  giveninits=false
]{biblatex}

\defbibheading{bibempty}{} % Suppress default bibliography headings

\DefineBibliographyStrings{spanish}{%
  backrefpage = {citado en página},
  backrefpages= {citado en páginas},
}

\usepackage[toc,section=section,xindy,numberline,style=altlist,savewrites=true,acronym,numberedsection]{glossaries}

\usepackage[utf8]{inputenc} %Codificacion de entrada

% Ruta donde buscar las figuras
\graphicspath{{figs/}}
\DeclareGraphicsExtensions{.pdf,.jpg,.png}


\geometry{
  a4paper,
  total={160mm,255mm},
  left=25mm,
  right=25mm,
  top=25mm,
  bottom=20mm
}

\newlength{\ancho}
\setlength{\ancho}{16cm}


\hypersetup{bookmarks=true,%
  bookmarksnumbered=true,%
  colorlinks,%
  citecolor=red,%
  filecolor=blue,%
  linkcolor=blue,%
  urlcolor=blue,%
  pdfstartview=FitH,%
  pdffitwindow=true,%
  pdfauthor=\@author}

\setlength{\parskip}{5pt}


\newcommand{\portada}{
  \pagestyle{empty}
  \makeatletter
  \centering % Centre everything on the title page
  % Use small caps for all text on the title page

  \begin{center}
    \includegraphics[width=0.7\ancho]{figs/ETSE.jpg}
  \end{center}

  \vspace*{1\baselineskip} % White space

  \begin{minipage}[h]{\ancho}
    \centering
    \LARGE
    \capsdef{T1/ppl/m/n/5-15}{\scshape}{.16em}{.6em}{.2em}
    \scshape \@titulacion
  \end{minipage}


  \vspace*{2\baselineskip} % White space

  \begin{center}
    \includegraphics[width=0.4\ancho]{figs/escudo_logo_UV.jpg}
  \end{center}

  \vspace*{3\baselineskip} % White space

  {\scshape \LARGE Trabajo Fin de Máster}

  \vspace*{2\baselineskip} % White space

  % ------------------------------------------------
  %   Title
  %------------------------------------------------
  \rule{\ancho}{1.6pt}\vspace*{-\baselineskip}\vspace*{2pt} % Thick horizontal rule
  \rule{\ancho}{0.4pt} % Thin horizontal rule

  \vspace{0.75\baselineskip} % Whitespace above the title

  \begin{minipage}[h]{\ancho}
    \centering
    \LARGE
    \capsdef{T1/ppl/m/n/5-15}{\scshape}{.16em}{.6em}{.2em}
    \scshape \@title
  \end{minipage}

  \vspace{0.75\baselineskip} % Whitespace below the title

  \rule{\ancho}{0.4pt}\vspace*{-\baselineskip}\vspace{3.2pt} % Thin horizontal rule
  \rule{\ancho}{1.6pt} % Thick horizontal rule

  \vfill

  \hspace*{0.15\ancho}\begin{minipage}[h]{0.85\ancho}
    \large
    \bfseries{\scshape \@authorlabel: \@author} % Author

    \vspace{0.5\baselineskip} % Whitespace below the editor list

    {\scshape \@tutorlabel: \@tutor} % Tutor

    \vspace{0.5\baselineskip} % Whitespace below the editor list

    {\scshape \@convocatoria}
  \end{minipage}
  \makeatother
}


\newcommand{\contraportada}{
  \pagestyle{empty}
  \makeatletter
  \centering % Centre everything on the title page
  \vspace*{0.2\baselineskip} % White space at the top of the page

  \begin{center}
    \includegraphics[width=\ancho]{figs/logo-contraportada.png}
  \end{center}

  \vspace*{\baselineskip} % White space

  \titulacion

  \vspace*{2\baselineskip} % White space

  {\scshape \LARGE Trabajo Fin de Máster}

  \vspace*{2\baselineskip} % White space

  % ------------------------------------------------
  %   Title
  %------------------------------------------------
  \rule{\ancho}{1.6pt}\vspace*{-\baselineskip}\vspace*{2pt} % Thick horizontal rule
  \rule{\ancho}{0.4pt} % Thin horizontal rule

  \vspace{2\baselineskip} % Whitespace above the title

  \begin{minipage}[h]{\ancho}
    \centering
    \LARGE
    \capsdef{T1/ppl/m/n/5-15}{\scshape}{.16em}{.6em}{.2em}
    \scshape \@title
  \end{minipage}

  \vspace{0.5\baselineskip} % Whitespace below the title

  \rule{\ancho}{0.4pt}\vspace*{-\baselineskip}\vspace{3.2pt} % Thin horizontal rule
  \rule{\ancho}{1.6pt} % Thick horizontal rule

  \vspace{5\baselineskip} % Whitespace after the title block

  \hspace*{0.15\ancho}\begin{minipage}[h]{0.85\ancho}
    \large
    \bfseries{\scshape \@authorlabel: \@author} % Author

    \vspace{0.5\baselineskip} % Whitespace below the editor list

    {\scshape \@tutorlabel: \@tutor} % Tutor

    \vspace{0.5\baselineskip} % Whitespace below the editor list
  \end{minipage}

  \vfill

  \rule{\ancho}{0.4pt}\vspace*{-\baselineskip}\vspace{3.2pt}

  \vspace{2\baselineskip} % Whitespace after the title block

  %   {\bf TRIBUNAL}

  %   \vspace{0.3\baselineskip} % Whitespace after the title block

  %   \flushleft PRESIDENTE/A: \hspace*{0.5\ancho}  VOCAL 1:

  %   \vspace{5\baselineskip}

  %   \flushleft VOCAL 2:      \hspace*{0.6\ancho}\begin{minipage}[t]{0.3\ancho}FECHA DE DEFENSA: \\[1cm]
  %                                                      CALIFICACIÓN:
  %                              \end{minipage}

  \vfill
  \makeatother
  \mdseries
}


\newcommand{\declaracion}
{
  \pagestyle{empty}
  \justify
  \makeatletter

  \vspace*{5cm}
  {\bf Declaración de autoría:}

  \vspace*{1cm}

  Yo, \@author, declaro la autoría del \cgls{tfm} titulado ``\@title{}'' y que el citado trabajo no infringe las leyes en vigor sobre propiedad intelectual. El material no original que figura en este trabajo ha sido atribuido a sus legítimos autores.

  \vspace*{1cm}

  Valencia, \today

  \vspace*{3cm}

  Fdo: \@author
  \vfill
  \makeatother
}

\newenvironment{resumen}
{\begin{center}\begin{tabular}{p{0.9\textwidth}}
  \hline\\
  {\bf Resumen:} \\[3mm]
}
{
  \\\\\hline
  \end{tabular}
  \end{center}
}

\newenvironment{abstract}
{\begin{center}\begin{tabular}{p{0.9\textwidth}}
  \hline\\
  {\bf Abstract:} \\[3mm]
}
{
  \\\\\hline
  \end{tabular}
  \end{center}
}


\newenvironment{resum}
{\begin{center}\begin{tabular}{p{0.9\textwidth}}
  \hline\\
  {\bf Resum:} \\[3mm]
}
{
  \\\\\hline
  \end{tabular}
  \end{center}
}


\newenvironment{agradecimientos}
{\begin{center}\begin{tabular}{p{0.9\textwidth}}
  \hline\\
  {\bf Agradecimientos:} \\[3mm]
}
{
  \\\\\hline
  \end{tabular}
  \end{center}
}


\lstdefinestyle{nonumbers} {numbers=none}
\lstset{basicstyle=\scriptsize\ttfamily}
\renewcommand{\UrlFont}{\scriptsize}

% Formato de los listados de código
\lstset{
  basicstyle=\ttfamily\small,
  columns=flexible,
  keywordstyle=\color{blue}\bf,
  commentstyle=\color{gray},
  stringstyle=\color{green},
  breaklines=true,inputencoding=utf8,
  frame=single,showstringspaces=false,
  style=nonumbers,extendedchars=true,
  literate={á}{{\'a}}1 {é}{{\'e}}1 {í}{{\'i}}1 {ó}{{\'o}}1 {ú}{{\'u}}1 {Á}{{\'A}}1 {É}{{\'E}}1 {Í}{{\'I}}1 {Ó}{{\'O}}1 {Ú}{{\'U}}1 {ñ}{{\~n}}1 {Ñ}{{\~N}}1,
}

\definecolor{enlaces}{rgb}{0.6,0.6,0.9}
\definecolor{colurl}{rgb}{0.34,0.36,0.60}

\hypersetup{
  colorlinks = true,
  linkcolor = enlaces,
  citecolor = enlaces,
  filecolor = enlaces,
  urlcolor = enlaces
}

\renewcommand{\lstlistingname}{Listado}
\renewcommand{\lstlistlistingname}{Indice de listados de código}

\renewcommand{\listingname}{Listado}% Listing -> Algorithm
%\renewcommand{\listlistingname}{Indice de listados de código}

\lstloadlanguages{html,java,sql,c,xml,tex,matlab}
\lstdefinestyle{numbers} {numbers=left, stepnumber=1, numberstyle=\tiny, numbersep=10pt}
\lstdefinestyle{nonumbers} {numbers=none}


%% Para acentos en listings con UTF8
\lstset{
  inputencoding=utf8,
  extendedchars=true,
  literate={á}{{\'a}}1 {é}{{\'e}}1 {í}{{\'i}}1 {ó}{{\'o}}1 {ú}{{\'u}}1 {Á}{{\'A}}1 {É}{{\'E}}1 {Í}{{\'I}}1 {Ó}{{\'O}}1 {Ú}{{\'U}}1 {ñ}{{\~n}}1 {Ñ}{{\~N}}1
}


%%%%%%%
%%%%%%%   DEFINICION DE UN CODIGO SIN KEYWORDS
%%%%%%%
\lstdefinelanguage{plain}
{morekeywords={},
  sensitive=false,
}

\pagestyle{fancy}

\fancypagestyle{tfg}{%
  %Información del capítulo en la parte exterior
  \fancyhead[EL,OR]{Capítulo \thechapter}
  % Información del número de página en la parte interior
  \fancyhead[OL,ER]{Página \thepage}
  \renewcommand{\headrulewidth}{1pt}
  \fancyfoot{}
}

\fancypagestyle{appendix}{%
  %Información del capítulo en la parte exterior
  \fancyhead[EL,OR]{Apéndices}
  % Información del número de página en la parte interior
  \fancyhead[OL,ER]{Página \thepage}
  \renewcommand{\headrulewidth}{1pt}
  \fancyfoot{}
}


\fancypagestyle{plain}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
}

% Definición de colores para los listados
\definecolor{lightgray}{rgb}{0.95, 0.95, 0.95}
\definecolor{darkgray}{rgb}{0.4, 0.4, 0.4}
\definecolor{editorGray}{rgb}{0.95, 0.95, 0.95}
\definecolor{editorOcher}{rgb}{1, 0.5, 0} % #FF7F00 -> rgb(239, 169, 0)
\definecolor{editorGreen}{rgb}{0, 0.5, 0} % #007C00 -> rgb(0, 124, 0)
\definecolor{orange}{rgb}{1,0.45,0.13}
\definecolor{olive}{rgb}{0.17,0.59,0.20}
\definecolor{brown}{rgb}{0.69,0.31,0.31}
\definecolor{purple}{rgb}{0.38,0.18,0.81}
\definecolor{lightblue}{rgb}{0.1,0.57,0.7}
\definecolor{lightred}{rgb}{1,0.4,0.5}
\definecolor{purple}{rgb}{0.65, 0.12, 0.82}
\definecolor{light-gray}{gray}{0.9}
\definecolor{gray}{gray}{0.5}
\definecolor{dark-gray}{gray}{0.8}

\addto\captionsspanish{\renewcommand{\tablename}{Tabla}}
\addto\captionsspanish{\def\listtablename{Índice de tablas}}
\renewcommand{\lstlistlistingname}{Índice de listados de código}

\newcommand{\ImageSource}[2]{
  \floatfoot{\sloppy\tiny\tt \colorbox{black}{\vrule height#2 depth0.8pt width0pt \color{white}Fuente}\fbox{#1}}
}

\newcommand*{\newdualentry}[5][]{%
  \newglossaryentry{main-#2}{name={#4},%
    text={#3\glsadd{#2}},%
    description={{#5}},%
    #1
  }%
  \newglossaryentry{#2}{
    type=\acronymtype,
    first={#4 (#3)},
    name={#3\glsadd{main-#2}},
    description={\glslink{main-#2}{#4}}
  }%
}