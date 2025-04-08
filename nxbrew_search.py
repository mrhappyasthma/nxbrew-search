import tkinter as tk
from tkinter import simpledialog, messagebox
import webbrowser
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import process


def fetch_game_list():
    url = 'https://nxbrew.net/Index/game-index/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    game_list = []
    for link in soup.find_all('a', href=True):
        title = link.text.strip()
        href = link['href']
        if title and href.startswith("https://nxbrew.net/"):
            game_list.append({'title': title, 'url': href})
    return game_list


def fuzzy_search(game_list, query, threshold=70):
    titles = [game['title'] for game in game_list]
    matches = process.extract(query, titles, limit=10)
    results = []
    for title, score in matches:
        if score >= threshold:
            result = next((g for g in game_list if g['title'] == title), None)
            if result:
                results.append(result)
    return results


def extract_download_sections(game_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(game_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    sections = []
    start_marker = None

    # Find the "Download Links" marker
    for p in soup.find_all('p'):
        if 'download links' in p.get_text(strip=True).lower():
            start_marker = p
            break

    if not start_marker:
        return []

    # Now go through following sibling divs
    current = start_marker
    while True:
        current = current.find_next_sibling()
        if not current or current.name != 'div':
            break

        columns = current.find_all('div', class_='wp-block-column')
        if len(columns) < 2:
            continue

        # First column = title
        title_tag = columns[0].find('p')
        title = title_tag.get_text(strip=True) if title_tag else 'Untitled'

        # Second column = links
        links = []
        for p in columns[1].find_all('p'):
            strong = p.find('strong')
            a = p.find('a', href=True)
            if strong and a:
                label = strong.get_text(strip=True)
                href = a['href']
                links.append((label, href))
            else:
                for a in p.find_all('a', href=True):
                    label = a.get_text(strip=True)
                    href = a['href']
                    if label and href:
                        links.append((label, href))

        if links:
            sections.append({
                'title': title,
                'links': links
            })

    return sections





class GameSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NXBrew Game Search")
        self.game_list = fetch_game_list()

        self.search_entry = tk.Entry(root, width=40)
        self.search_entry.pack(pady=10)

        self.search_btn = tk.Button(root, text="Search", command=self.search)
        self.search_btn.pack()

        self.results_listbox = tk.Listbox(root, width=60, height=10)
        self.results_listbox.pack(pady=10)

        self.select_btn = tk.Button(root, text="Show Downloads", command=self.show_downloads)
        self.select_btn.pack(pady=5)

    def search(self):
        query = self.search_entry.get()
        if not query:
            return
        results = fuzzy_search(self.game_list, query)
        self.results_listbox.delete(0, tk.END)
        for result in results:
            self.results_listbox.insert(tk.END, f"{result['title']} | {result['url']}")
        self.search_results = results

    def show_downloads(self):
        selected = self.results_listbox.curselection()
        if not selected:
            return
        index = selected[0]
        game = self.search_results[index]
        sections = extract_download_sections(game['url'])

        if not sections:
            messagebox.showinfo("No links found", "No download links found.")
            return

        win = tk.Toplevel(self.root)
        win.title(f"Downloads - {game['title']}")

        for section in sections:
            tk.Label(win, text=section['title'], font=('Arial', 10, 'bold')).pack(anchor='w', padx=10, pady=4)
            for label, url in section['links']:
                link_label = tk.Label(win, text=f"• {label}", fg="blue", cursor="hand2", anchor="w", justify="left")
                link_label.pack(anchor='w', padx=20)
                link_label.bind("<Button-1>", lambda e, url=url: webbrowser.open_new(url))



if __name__ == '__main__':
    root = tk.Tk()
    app = GameSearchApp(root)
    root.mainloop()
