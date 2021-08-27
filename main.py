from collections import defaultdict
import json
import requests
from bs4 import BeautifulSoup


base_url = 'https://kolesa.kz'
search_url = base_url + '/cars/?page=%d'


def parse_proposal(proposal) -> dict:
    """ Парсит элемент предложения 
    Вполне вероятно что появятся дубликаты, 
    так как новые объявления поевляются достаточно быстро
    """
    info_top = proposal.find("div", class_="a-info-top")
    info_mid = proposal.find("div", class_="a-info-mid")
    info_bot = proposal.find("div", class_="a-info-bot")

    url = info_top.find('a', class_='list-link ddl_product_link').get('href')
    title = info_top.find('a', class_='list-link ddl_product_link').text.strip()
    price = info_top.find('span', class_='price').text.replace(u'\xa0', '').strip()

    info = [s.strip() for s in info_mid.find('p').strings]
    description = info_mid.find('div', class_='a-search-description').text.strip()
    month_price = info_mid.find('div', class_='month-price')
    creditable = True if month_price else False

    city = info_bot.find('div', class_='list-region').text.strip()
    date = info_bot.find('span', class_='date').text.strip()

    return {
        'url': base_url + url,
        'title': title,
        'price': int(price[:-1]),
        'creditable': creditable,
        'info': info,
        'description': description,
        'city': city,
        'date': date,
    }


def parse_proposals(max_proposals, pages) -> defaultdict:
    """ Ищет все предложения на странице и передаёт их для парсинга """
    result = defaultdict(list)
    current_proposal = 0

    for page in range(1, pages):
        print('Parse page', page)
        response = requests.get(search_url % page)
        soup = BeautifulSoup(response.content, 'html.parser')
        proposals = soup.find_all('div', class_=['row vw-item list-item a-elem', 'blue', 'yellow'])
        for proposal in proposals:
            proposal_data = parse_proposal(proposal)
            result[proposal_data['city']].append(proposal_data)

            current_proposal += 1
            if max_proposals > 0 and current_proposal >= max_proposals:
                return result

    return result


if __name__ == '__main__':
    max_proposals = int(input('Количество предложений для обработки (-1 для всех): '))

    response = requests.get(search_url % 1)
    soup = BeautifulSoup(response.content, 'html.parser')

    # На странице есть пагинатор который ограничен 1000 страницами, 
    # но по факту можно смотреть и дальше, но уже прописывая в url вручную
    # для большей уверености просто смотрим максимальное количество страниц которое даёт сайт
    pages = int(soup.find('div', class_='pager').find_all('li')[-1].text)

    parse_result = parse_proposals(max_proposals, pages)

    with open('result.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(parse_result, ensure_ascii=False, indent=4))
