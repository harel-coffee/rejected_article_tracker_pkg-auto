from fuzzywuzzy import fuzz
import numpy as np
from gensim.parsing.preprocessing import preprocess_string, strip_tags
from gensim.utils import deaccent



class SearchResult:
    def __init__(self, match_article: dict, query_article: dict,  clf, rank: int):
        """
        :param match_article: Article details from search provider (e.g. CrossRef)
        :param query_article: The input article (e.g. from the user)
        :param clf: The classifier to score how similar the articles are.
        :param rank:
        """
        self.query_article = query_article
        self.match_article = match_article
        self.clf = clf
        self.rank = rank

    def to_dict(self) -> dict:
        match_article = self.match_article
        match_article['authors_list'] = self.authors_list(match_article['author'])
        match_article.update(self.match_names(
                                        query_authors=self.query_article['authors'], 
                                        match_authors=self.match_article['authors_list']
                                        )
                            )
        match_article['similarity'] = fuzz.ratio(self.query_article['manuscript_title'],
                                           match_article['title']) if 'title' in match_article else 0
        match_article['classifier_score'] = self.classify(match_article)
        match_article['rank'] = self.rank
        return match_article

    @staticmethod
    def authors_list(authors: list) -> list:
        match_authors = []
        for author in authors:
            given = author.get('given', '')
            family = author.get('family', '')
            match_authors.append(given + '+' + family)
        return match_authors

    def pre_process_name(self, name):
        """
        Takes a string as input, removes accents and 
        converts to lowercase
        """
        name = deaccent(name)
        name = name.lower()
        first_name = name[0]
        last_name = name[name.rfind('+') + 1:]
        first_name = first_name.replace('-','').replace('\'','').replace(' ','')
        first_init = first_name[0]
        last_name = last_name.replace('-','').replace('\'','').replace(' ','')
        name = (first_init, last_name)
        return name

    # @staticmethod
    def match_names(self, match_authors, query_authors):
        names1 = list()
        for name in query_authors.split(', '):
            name = self.pre_process_name(name)
            names1.append(name)
        
        names2 = list()
        for name in match_authors:
            name = self.pre_process_name(name)
            names2.append(name)
        
        names2 = set(names2)

        return {
            'author_match_one': int(any(name in names2 for name in names1)),
            'author_match_all': int(all(name in names2 for name in names1)),
        }

    def classify(self, match_article: dict):
        predictors = [
            match_article['similarity'],
            match_article['author_match_all'],
            match_article['score'],
            self.rank,
            len(self.match_article['authors_list'])
        ]
        X = np.array([float(x) for x in predictors])
        clf_scores = self.clf.predict_proba(np.reshape(X, (1, 5)))
        score = clf_scores[0][1]
        return score
