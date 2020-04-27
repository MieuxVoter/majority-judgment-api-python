#language: fr
@fr
Fonctionnalité: Décrire les comportements des étapes des scénarios
  Dans le but de …
  En tant que …
  Nous souhaitons …


Scénario: Requérir la présence à priori de citoyen⋅nes
  # New keyword Sachant has not yet propagated to our behave version
  #Sachant qu'il ne devrait y avoir aucun citoyen dans la base de données
  # So we use the less idiomatic equivalent
  Étant donné qu'il ne devrait y avoir aucun citoyen dans la base de données
  Étant donné un citoyen nommé Michel Balinski
  Alors il devrait y avoir un citoyen dans la base de données


Scénario: Requérir la présence à priori de scrutins
  Étant donné qu'il ne devrait y avoir aucun scrutin dans la base de données
  Étant donné un scrutin comme suit:
  """
  titre: Responsable de l'animation du chantier Constituance Algorithmique
  candidats:
    - Pierre-Louis Guhur
    - Chloé Ridel
    - Dominique Merle
  """
  Alors il devrait y avoir un scrutin dans la base de données


# Scénario: Soumettre un nouveau scrutin
