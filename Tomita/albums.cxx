#encoding "utf-8"
#GRAMMAR_ROOT S

Title -> Word<h-reg1>+;
Title -> Word<h-reg1>+ Word Word<h-reg1>+;
Title -> Word<h-reg1, quoted>;
Title -> Word<h-reg1, l-quoted> Word<r-quoted>;
Title -> Word<h-reg1, l-quoted, ~r-quoted> AnyWord<~r-quoted>+ Word<~l-quoted, r-quoted>;

TranslateDescriptor -> LBracket Word* Punct Comma Hyphen* AnyWord+ interp(Album.Translation::not_norm) RBracket;
AlbumDescriptor -> Word* Word<wff=/альбом(-.+)?/>;

SingerDescriptor -> Word<h-reg1>+ interp(Album.Singer) Punct | Comma;
SingerDescriptor -> AnyWord* Noun<kwtype="singer"> SingerDescriptor;

Day -> AnyWord<wff=/([1-2]?[0-9])|(3[0-1])/>;
Month -> Noun<kwtype="month">; 

YearDescr -> "год" | "г. ";
Year -> AnyWord<wff=/[1-2]?[0-9]{3}/>;
Year -> Year YearDescr;

Date -> Year;
Date -> Day Month Year;

DateDescriptor -> AnyWord+ Date interp(Album.Date::not_norm);

S -> Title interp(Album.Name::not_norm) TranslateDescriptor* Hyphen AlbumDescriptor SingerDescriptor DateDescriptor*; 