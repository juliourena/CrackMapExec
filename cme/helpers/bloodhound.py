#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def add_user_bh(user, domain, logger, config):
    users_owned = []
    if isinstance(user, str):
        users_owned.append({'username': user.upper(), 'domain': domain.upper()})
    else:
        users_owned = user
    if config.get('BloodHound', 'bh_enabled') != "False":
        try:
            from neo4j.v1 import GraphDatabase
        except:
            from neo4j import GraphDatabase
        from neo4j.exceptions import AuthError, ServiceUnavailable
        uri = "bolt://{}:{}".format(config.get('BloodHound', 'bh_uri'), config.get('BloodHound', 'bh_port'))

        driver = GraphDatabase.driver(uri, auth=(config.get('BloodHound', 'bh_user'), config.get('BloodHound', 'bh_pass')), encrypted=False)
        try:
            with driver.session() as session:
                with session.begin_transaction() as tx:
                    for info in users_owned:
                        if info['username'][-1] == '$':
                            user_owned = info['username'][:-1] + "." + info['domain']
                            account_type = 'Computer'
                        else:
                            user_owned = info['username'] + "@" + info['domain']
                            account_type = 'User'

                        result = tx.run(
                            "MATCH (c:{} {{name:\"{}\"}}) RETURN c".format(account_type, user_owned))

                        if result.data()[0]['c'].get('owned') in (False, None):
                            logger.debug("MATCH (c:{} {{name:\"{}\"}}) SET c.owned=True RETURN c.name AS name".format(account_type, user_owned))
                            result = tx.run(
                                "MATCH (c:{} {{name:\"{}\"}}) SET c.owned=True RETURN c.name AS name".format(account_type, user_owned))
                            logger.highlight("Node {} successfully set as owned in BloodHound".format(user_owned))
        except AuthError as e:
            logger.error(
                "Provided Neo4J credentials ({}:{}) are not valid.".format(config.get('BloodHound', 'bh_user'), config.get('BloodHound', 'bh_pass')))
            return
        except ServiceUnavailable as e:
            logger.error("Neo4J does not seem to be available on {}.".format(uri))
            return
        except Exception as e:
            logger.error("Unexpected error with Neo4J")
            logger.error("Account not found on the domain")
            return
        driver.close()