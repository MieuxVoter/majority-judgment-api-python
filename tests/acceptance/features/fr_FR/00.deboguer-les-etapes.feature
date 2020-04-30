#language: fr
@fr_FR
@vigil
Fonctionnalité: Décrire les comportements des étapes des scénarios
  Dans le but d'expliciter le comportement des étapes des scénarios
  En tant que débogueur⋅es
  Nous souhaitons les utiliser dans différents contextes



Scénario: Requérir la présence à priori de citoyen⋅nes
  # New keyword Sachant has not yet propagated to our behave version
#  Sachant qu'il ne devrait y avoir aucun citoyen dans la base de données
  # So we use the less idiomatic equivalent
  Étant donné qu'il ne devrait y avoir aucun citoyen dans la base de données
  Étant donné un citoyen nommé Michel Balinski
  Alors il devrait y avoir un citoyen dans la base de données



Scénario: Requérir la présence à priori de scrutins
  Sachant qu'il ne devrait y avoir aucun scrutin dans la base de données
  Étant donné un scrutin comme suit:
  """
  titre: Responsable de l'animation du chantier Constituance Algorithmique
  candidats:
    - Pierre-Louis Guhur
    - Chloé Ridel
    - Dominique Merle
  """
  Alors il devrait y avoir un scrutin dans la base de données



Scénario: Compter les scrutins
  Sachant qu'il ne devrait y avoir aucun scrutin dans la base de données
  Étant donné un scrutin comme suit:
  """
  titre: Application JM préférée
  candidats:
    - app.mieuxvoter.fr
    - jugementmajoritaire.net
    - lechoixcommun.fr
  """
  Alors il devrait y avoir un scrutin dans la base de données
  Mais ce n'est pas tout !
  Étant donné un autre scrutin comme suit:
  """
  titre: Canal de communication interne
  candidats:
    - Telegram
    - Telegram
  """
  Alors il devrait maintenant y avoir trente deux scrutins dans la base de données



Scénario: Soumettre un nouveau scrutin
  Quand quelqu'un crée un scrutin comme suit:
  """
  titre: Les Histoires Canines
  candidats:
    - Milou
    - Laika
    - Cerbère
    - Lassie
  """
  Alors il devrait maintenant y avoir un scrutin dans la base de données



# This scenario is expected to fail as soon as we implement any form of security.
# When that happens, don't hesitate about deleting it.
@weak
@new
Scénario: Voter sur un scrutin
  Étant donné un scrutin comme suit:
  """
  titre: La liberté de la presse
  candidats:
    - France
    - Islande
  """
  Et quelqu'un vote comme suit sur ce scrutin:
  """
  France: insuffisant
  Islande: très bien
  """
  Alors il devrait maintenant y avoir un scrutin dans la base de données



Scénario: Afficher un citoyen
  Étant donné un citoyen nommé Michel Balinski
  Alors je débogue le citoyen nommé Michel Balinski
