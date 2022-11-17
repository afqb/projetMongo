# -*- coding: utf-8 -*-
"""
Created on Sat Oct 29 12:27:31 2022

@author: alexi
"""

#On importe les librairies
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime
import sys

#Connexion sur notre db mongodb
client = MongoClient("mongodb+srv://alexis:root@cluster0.xwlzjbj.mongodb.net/?retryWrites=true&w=majority", server_api=ServerApi('1'))
db = client.vls

#----------------------------------------------------------------------------------------------------------------
#Ensemble des fonctions utilisées dans ce projet


def stations_a_proximite(coordonnes_user):

        liste_stations=[]

        #On récupère le nom des 5 stations les plus proches des coordonnées renseignées par l'utilisateur
        req_station=db.stations.find(
                {
                    'geometry': 
                        { 
                            '$nearSphere': 
                                {
                                    '$geometry': {'type': "Point", 'coordinates': coordonnees_user},
                                    '$minDistance': 0,
                              }
                      } 
                 }, 
                    {"_id":0,"name":1}
                    ).limit(5)
            
        #Pour chacune de ces station, on récupère le nombre de vélos et d'emplacements disponibles pour informer l'utilisateur
        for i in range (5):
            #On récupère l'id de la station pour effectuer une relation entre la collection datas et stations
            _id=db.stations.find({'name':req_station[i]['name']},{'_id':1})[0]['_id']
            req_data=db.datas.find({ 'station_id': _id },{'_id':0,'date':0,'station_id':0}).sort( "date", -1 ).limit(1)

            liste_stations+=[[req_station[i]['name'],req_data[0]['bike_availbale'],req_data[0]['stand_availbale']]]

        #On affiche chaque station avec le nom, le nombre d'emplacements et de vélos disponibles
        for doc in range (5):
            print("Station "+str(doc+1)+" : "+liste_stations[doc][0]+" ("+str(liste_stations[doc][1])+' vélos disponibles / ' + str(liste_stations[doc][2]) + ' places disponibles)')  


def nom_de_station(nom):
    #Fonction utilisée pour recherhcer un nom de station en ne tapant que quelques lettres
    
    #Requête pour obtenir le nom des stations selon l'entrée de l'uilisateur
    req = db.stations.find({'name':{'$regex':nom+'.*','$options':'i'}},{'_id':0,'name':1})
    
    print("\nVoici la liste des stations correspodant à votre recherche :\n")
    #Affichage des noms complets de station
    for doc in req:
        print('\t+ '+doc['name'])


def supprimer_station(nom_complet):
    #Fonction utiisée pour supprimer une station de la db
    
    #On vérifie l'existence de la station
    if len(list(db.stations.find({'name': nom_complet})))==0:
        print("\nLa station est introuvable, veuillez réessayer.")
    
    #Si elle existe on la supprime
    else :
        db.stations.delete_one({'name':nom_complet})
        print('\nLa station '+nom_complet+' , a été supprimé avec succès')
       
        
def modifier_station(nom_complet):
    #Fonction utilisée pour modifier les valeurs d'une station
    
    #Premièrement sur la collection stations
    print("\nEntrez les nouvelles valeurs.")
    nom=input("Nouveau nom : ")
    taille=int(input("Nouvelle capacité globale : "))
    tpe=bool(input("Présence d'un tpe ? Répondre True ou False : ").lower()=='true')
    db.stations.update_one({'name':nom_complet},{'$set':{'name':nom,'size':taille,'tpe':tpe}})
    
    #Puis sur la collection datas en ajoutant une nouvelle ligne, avec la date actuelle afin d'actualiser les données
    velos_dispo=int(input("Nombre de vélos disponibles : "))
    places_dispo=int(input("Nombre d'emplacements disponibles : "))    
    _id=db.stations.find({'name':nom},{'_id':1})[0]['_id']
    
    date_actuelle = datetime.datetime.now()

    db.datas.insert_one({ 'date':date_actuelle,'station_id': _id,'bike_availbale':velos_dispo,'stand_availbale':places_dispo})
    print("\n----Modification effectuée !----")
    affichage_station(nom)
    
def affichage_station(nom_complet):
    #Fonction utilisée pour afficher les données sur une station en renseignant le nom complet de la station
    
    print("\nVoici les informations de cette station :\n")
    
    station_dict=db.stations.find({'name':nom_complet},{'_id':0,'geometry':0,'source':0})[0]
    _id=db.stations.find({'name':nom_complet},{'_id':1})[0]['_id']
    station_dict.update(db.datas.find({ 'station_id': _id },{'_id':0,'date':0,'station_id':0}).sort( "date", -1 ).limit(1)[0])
    
    print("Nom : "+station_dict["name"]+"\nTaille : "+str(station_dict["size"])+"\nPrésence de TPE : "+str(station_dict["tpe"])+"\nVélos disponibles : "+str(station_dict["bike_availbale"])+"\nPlaces disponibles : "+str(station_dict["stand_availbale"]))
    
def desactiver_station(nom_complet):
    #Pour désactiver une station, on enlève la possibilité de prendre ou déposer un vélo. On passe donc à 0 le nombre de vélos et d'emplacements disponibles 
    _id=db.stations.find({'name':nom_complet},{'_id':1})[0]['_id']
    
    date_actuelle = datetime.datetime.now()

    db.datas.insert_one({ 'date':date_actuelle,'station_id': _id,'bike_availbale':0,'stand_availbale':0})

def ratio_stations():
    #Fonction qui prend quelques minutes
    #On choisi arbitrairement le jour de la semaine au 14
    day=14
    
    #On récupère le nom des stations de vlille
    name_stations=list(db.stations.find({},{'_id':0,'size':0,'geometry':0,'source':0,'tpe':0}))
    
    #On initialise quelques variables et dictionnaires
    count=0
    ratio_dict={}
    index_dict={}
    error=0
    
    #Pour chaque jour de la semaine ouvrée
    for i in range (0,5):
        date1 = datetime.datetime(2022, 11, day+i, 18, 0, 0, 0)
        date2 = datetime.datetime(2022, 11, day+i, 19, 0, 0, 0)
    
        #Pour chaque station de vlille    
        for doc in name_stations:
            
            #On récupère le nom et la taille de la station dans un dictionnaire
            station_dict=db.stations.find({'name':doc['name']},{'_id':0,'geometry':0,'source':0,'tpe':0})[0]
            #On récupère l'identifiant de la station
            _id=db.stations.find({'name':doc['name']},{'_id':1})[0]['_id']
            
            #On vérifié qu'il existe une donnée pour le jour étudié entre 18h et 19h
            try :
                #On ajoute au dictionnaire le nombre de vélos disponibles pour la station étudié sur le jour étudié entre 18h et 19h
                station_dict.update(db.datas.find({ 'station_id': _id, 'date': {'$gte':date1, "$lt":date2} },{'_id':0,'date':0,'station_id':0,'stand_availbale':0}).sort( "date", -1 ).limit(1)[0])
                #On calcul le ratio (nombre de vélos disponibles / taille totale)
                ratio=round(station_dict['bike_availbale']/station_dict['size'],2)
    
                #Si un ratio est déjà présent dans le dictionnaire, on l'additionne à celui existant. 
                #On met à jour le dictionnaire des index qui attribue a chaque nom de station le nombre de jours ou une donnée a été recueillis sur les 5 jours étudiés
                if (station_dict['name'] in ratio_dict):
                    ratio_dict[station_dict['name']]=ratio_dict[station_dict['name']]+ratio
                    index_dict[station_dict['name']]=index_dict[station_dict['name']]+1
                #Sinon on attribu le ratio au nom de la station
                else:
                    ratio_dict[station_dict['name']]=ratio
                    index_dict[station_dict['name']]=1
                    
            except IndexError:
                error=1
    
    #Moyenne du ratio sur le nombre de jours de la semaine ouvrée dont on a une donnée sur les vlille de 18h à 19h
    for i in ratio_dict:
        ratio_dict[i]=ratio_dict[i]/index_dict[i]
        
        #Si le ration est inférieur à 20%, on affiche le nom de la station avec le ratio
        if ratio_dict[i]<0.2:
            print(i+' : '+str(ratio_dict[i]*100)+ ' %')
        count+=1
                
    if count==0:
        print('Toutes les stations comportent au moins 20% de vélos disponibles')
    
#----------------------------------------------------------------------------------------------------------------

#Choix des coordonnées GPS par l'utilisateur
latitude = input("Quelle est votre position ?\n\nCommencez par renseigner la latitude : ")
longitude = input("Renseignez également la longitude : ")

#On stocke ces valeurs dans une liste en vérifiant que les valeurs correspondent à des coordonnées GPS
try :
    coordonnees_user = [float(latitude),float(longitude)]
    if not(-90<float(latitude)<90 and -180<float(longitude)<180):
        print("\nVeuillez renseigner des coordonnées GPS valides")
        sys.exit()
except ValueError:
    print("\nVeuillez renseigner des coordonnées GPS valides")
    sys.exit()

#Création d'un index 2dsphere
db.stations.create_index([('geometry','2dsphere')])

#----------------------------------------------------------------------------------------------------------------
#Programme intéractif avec l'utilisateur

choix=1
while choix!=0:
    print("\n\n\n------------------------------------------------") 
    print("Que souhaitez-vous faire ?\n0 : Quitter\n1 : Montrer les 5 stations les plus proches\n2 : Chercher un nom de station\n3 : Afficher les informations d'une station\n4 : Supprimer une station\n5 : Mettre à jour une station\n6 : Désactiver les stations de la catho\n7 : Afficher les statistiques de chaque station entre 18h et 19h du lundi au vendredi")    
    try:
        choix=int(input("Entrer le numéro correspondant à votre choix : "))
    except ValueError:
        print('Entrer un entier valide')

    if choix==1:
        stations_a_proximite(coordonnees_user)
 
    if choix==2:
        print("\nQuelle station souhaitez vous ? Entrer le nom exact, ou les premières lettres")
        nom=input()
        nom_de_station(nom)
        
    if choix==3:
        nom_complet=input("Entrer le nom complet de la station :")
        if len(list(db.stations.find({'name': nom_complet})))==0:
            print("\nLa station est introuvable, veuillez réessayer en vérifiant l'orthographe saisi.")
        else :
            affichage_station(nom_complet)
        
    if choix==4:
        nom_complet=input("Entrer le nom complet de la station :")
        supprimer_station(nom_complet)
    
    if choix==5:
        nom_complet=input("Entrer le nom complet de la station :")
        if len(list(db.stations.find({'name': nom_complet})))==0:
            print("\nLa station est introuvable, veuillez réessayer.")
        else :
            affichage_station(nom_complet)
            modifier_station(nom_complet)

    if choix==6:
        #On créé un polygone avec les stations suivantes : Jean Sans Peur - Champ de Mars - Place Catinat - Cormontaigne - Metro Gambetta - Jean Sans Peur
        coord=[[[3.05816,50.632367],[3.0508558,50.6379088],[3.041209,50.63413],[3.039911,50.62624],[3.051729,50.62614],[3.05816,50.632367]]]
        
        #On recupere les stations qui se trouvent dans le polygone
        req=db.stations.find(
            {'geometry': 
             {"$geoWithin": 
              {"$geometry": 
               {"type": "Polygon","coordinates": coord }
              }
             }
            })
        
        #On passe le nombre de vélos et emplacements disponible à 0 pour toutes ces stations
        for doc in req:
            desactiver_station(doc['name'])

        print("\nLes stations de la catho ont été désactivées.")
         
    if choix==7:
        print("NB : La fonction peut prendre quelques minutes d'exécution ...\n")
        print("Stations possédant un ratio inférieur à 20% du nombre de vélos disponibles par rapport à la capacité maximale entre 18h et 19h pour la semaine du 14/11 au 18/11 :\n")
        ratio_stations()

