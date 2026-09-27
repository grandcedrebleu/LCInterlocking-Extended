# LCInterlocking Extended 1.3.0-alpha.7

Prototype pour FreeCAD 1.1.3 — doigts croisés débordants à angle oblique.

## Installation complète

1. Fermer FreeCAD.
2. Déplacer l’ancien dossier LCInterlocking-Extended hors du dossier Mod pour
   le conserver comme sauvegarde (ne pas laisser deux copies actives dans Mod).
3. Copier le dossier LCInterlocking-Extended fourni dans :
   le dossier Mod de ton profil FreeCAD (sous Windows : %APPDATA%\FreeCAD\v1-1\Mod)
4. Relancer FreeCAD et choisir Laser Cut Interlocking Extended.
5. Le menu LCInterlocking Extended et la barre Tab contiennent la nouvelle
   commande « Doigts croisés obliques (prototype) ».

Aucun fichier Python à remplacer individuellement. Retour à la version précédente :
fermer FreeCAD, retirer le nouveau dossier et remettre le dossier sauvegardé.

## Premier essai conseillé : démonstration

Après avoir activé l’atelier, ouvrir avec Macro → Macros → parcourir/sélectionner
le fichier test/extended/Demo_doigts_obliques.FCMacro dans le dossier installé,
puis l’exécuter. On peut aussi ouvrir ce fichier par Fichier → Ouvrir puis
utiliser la commande d’exécution de macro.

Il crée un nouveau document contenant deux panneaux à 60°, en 3 et 5 mm,
avec six bandes alternées et des dépassements de 3 mm.
Double-cliquer sur le groupe DoigtsObliques pour ouvrir les paramètres.

## Sur un document personnel

- Utiliser deux panneaux rectangulaires pleins ou deux Links vers ces panneaux, directement à la racine du document.
- Sélectionner un chant terminal de A, puis Ctrl + clic sur le chant terminal de B.
  Il s’agit des petites faces rectangulaires à l’extrémité des panneaux, pas de
  leurs grandes faces. Les deux chants doivent suivre l’axe du croisement.
- Cliquer sur Doigts croisés obliques.
- Les originaux sont conservés et masqués. Deux résultats apparaissent dans un groupe.
- Régler les paramètres dans la fenêtre, puis cliquer sur Aperçu et Valider.
- Pour les modifier ensuite, double-cliquer sur le groupe dans l’arbre.
- Annuler abandonne la création ou restaure les réglages précédents.
- Pour un ancien groupe, sélectionner le groupe et relancer la commande si le double-clic ne fonctionne pas encore.
- Pour exporter, sélectionner uniquement les deux résultats ; vérifier le tracé 2D.

Sur Test-Assemblage(1).FCStd, les chants proches du raccord correspondent dans
l’ordre BREP examiné à Face2 de Extrude et Face1 de Extrude001. Privilégier la
sélection visuelle des chants ; la numérotation peut évoluer après une modification.

## Paramètres

| Propriété | Signification | Défaut |
|---|---|---|
| SizingMode | Nombre de bandes ou largeur souhaitée | Nombre de bandes |
| RequestedWidth | Largeur cible des bandes avant jeu ; active en mode largeur | 10 mm |
| BandCount | Nombre total de bandes alternées, pas nombre de doigts par panneau | 6 |
| OverhangA / OverhangB | Dépassement au-delà de la limite du croisement dans la direction du panneau | 3 mm |
| FitGap | Jeu total entre deux doigts voisins, suivant l’axe du joint | 0,05 mm |
| Invert | Permute les bandes conservées sur A et B | Non |
| AcuteAngle | Angle aigu entre les plans, calculé ; 120° donne ici 60° | Lecture seule |
| BandWidth | Largeur d’une bande avant jeu, calculée sur la longueur commune | Lecture seule |
| Status | Résultat du calcul ou motif de refus | Lecture seule |

Avec six bandes, chaque panneau porte trois doigts dans la zone commune.
Choisir soit le nombre de bandes (2 à 100), soit une largeur souhaitée.
En mode largeur, le nombre est arrondi et limité à 2–100, puis la largeur réelle
est ajustée pour répartir régulièrement les bandes sur la longueur commune.
La fenêtre affiche cette largeur réelle après Aperçu. Un nombre impair donne
un doigt de plus sur un des panneaux ; Inverser permute cette répartition.

Le dépassement est mesuré dans le plan du panneau. À angle oblique, il n’est
pas une distance normale constante à l’autre panneau. La référence est le
point de croisement le plus avancé sur toute l’épaisseur. Un chant existant
peut être prolongé ou raccourci pour obtenir cette valeur.

Les découpes sont perpendiculaires aux grandes faces des panneaux. Cela peut
laisser de petits vides en coin dans un assemblage oblique : le calcul respecte
la découpe laser 2D, il ne crée pas des chants biseautés.

FitGap n’est PAS une compensation du trait laser. Ce prototype n’applique pas
les réglages matériau de MultiJoin. Appliquer la compensation de coupe une seule
fois dans le logiciel de découpe, après un coupon d’essai adapté au bois utilisé.
La marge traversante de MultiJoin ne commande pas cette nouvelle fonction.

## Périmètre de cette version

- Panneaux plans à épaisseur constante, faces planes, un solide. Le chant choisi doit être terminal, entier et rectangulaire.
- Épaisseurs déduites de la géométrie ; 3/3, 5/5 et 3/5 mm testés.
- Chants parallèles à la ligne d’intersection des plans.
- Angles aigus entre plans d’au moins 10°. Essais réalisés de 30° à 150°.
- Links vers des panneaux rectangulaires acceptés à la racine du document. Les conteneurs et sélections imbriquées ne sont pas pris en charge.
- Plusieurs raccords successifs sont possibles sur des chants entiers distincts. Pas de reprise sur un chant déjà découpé, ni de génération automatique de plusieurs couches.
- Pas de simulation de ponçage ni de validation de résistance mécanique.
- Les références de faces peuvent devenir obsolètes si les sources sont reconstruites.
- En cas d’erreur au recalcul, les formes résultats sont vidées pour éviter
  d’afficher un ancien résultat comme s’il correspondait aux nouveaux paramètres.

## Vérifications

18 cas de géométrie exécutés avec le module de production et un adaptateur
FreeCAD Part → CadQuery/OpenCascade : angles 30/45/60/90/120/150°, épaisseurs
3/3, 5/5 et 3/5 mm. Validité, un seul solide par panneau, absence de collision,
présence alternée des doigts et ouverture des encoches contrôlées.

Un calcul sur les BREP du fichier fourni a également réussi. Les placements
contenus dans les BREP ont été conservés, sans appliquer deux fois les translations.

FreeCAD n’est pas installé dans l’environnement de développement : l’interface,
le recalcul paramétrique et la sauvegarde/réouverture doivent encore être vérifiés
sur FreeCAD 1.1.3. Ce paquet est une préversion, pas une release stable.
La macro Verifier_doigts_obliques.FCMacro rejoue les 18 cas géométriques dans FreeCAD.

## Traçabilité
Les sources sont maintenues sur main ; le build génère la branche dist.
Les résultats de validation et les limites figurent dans CHANGELOG.md.

## Correction alpha.3
Les encoches terminales atteignent les bords réels si leur décalage le long du
joint est de 0,10 mm au plus. Cela élimine les fines languettes dues aux petites
différences de longueur. Les décalages plus grands restent inchangés.

## Interface alpha.4
Fenêtre de paramètres avec Aperçu, Valider et Annuler ; édition par double-clic.
Réglages : nombre de bandes ou largeur souhaitée, dépassements A/B, jeu et inversion.
Les épaisseurs et l’angle sont mesurés sur les panneaux ; leur modification se fait sur les sources.
Le test du proxy réel avec adaptateur OpenCascade vérifie les deux modes de dimensionnement.
Les interactions Qt, l’annulation FreeCAD et la sauvegarde/réouverture ne sont pas validées ici.

## Correction alpha.5 — Links
La sélection conserve les occurrences Link. La géométrie et le chant sont résolus
avec Part.getShape, avec leur transformation, sans appliquer deux fois le placement.
Les résultats sont propres à l’assemblage ; la géométrie du panneau source et les
autres occurrences ne sont pas modifiées. Les deux Links sélectionnés sont masqués
à la validation comme les panneaux ordinaires.
Sélectionner les chants directement sur les deux Links visibles, avec Ctrl.
Les Links à la racine sont acceptés ; les conteneurs, tableaux de Links et chemins
de sélection imbriqués ne font pas partie de ce correctif.
La macro Verifier_links_obliques.FCMacro contrôle LinkTransform Non/Oui,
la conservation de la source et le recalcul après déplacement. Cette macro native
est fournie mais n’a pas pu être exécutée ici (FreeCAD absent).
Références API :
https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/Part/App/AppPartPy.cpp
https://freecad.github.io/SourceDoc/d4/dca/classGui_1_1SelectionSingleton.html

## Correction alpha.6 — sélection des faces
Les noms enrichis de FreeCAD (par exemple ;#…F.Face3) sont désormais acceptés,
ainsi que les noms classiques Face3. La référence complète est conservée.
Le refus observé concernait aussi bien une extrusion qu’un Link.
Sélectionner les deux chants avec Ctrl puis lancer la commande comme auparavant.
Les deux références exactes transmises ont été testées à travers le proxy avec
un résolveur simulé. La résolution native FreeCAD reste à vérifier sur le poste.

## Alpha.7 — ajouter un second raccord
Sélectionner le chant encore entier du résultat du premier raccord (panneau orange
ou bleu), puis Ctrl + clic sur le chant du troisième panneau ou Link.
Lancer la commande, Aperçu, puis Valider. Le nouveau résultat conserve les doigts
existants sur l’autre extrémité. Sélectionner l’ancien panneau source créerait un
raccord indépendant sans reprendre ses premières découpes.
Essai réalisé avec LCIE_FingersB002 du fichier utilisateur et la géométrie du Link :
angle 60°, un solide valide par résultat, absence de collision, conservation de la
moitié opposée du panneau par différence symétrique inférieure à 1e-5 mm³.
Test réalisé sur les BREP via CadQuery/OpenCascade ; interface native FreeCAD non exécutée.
