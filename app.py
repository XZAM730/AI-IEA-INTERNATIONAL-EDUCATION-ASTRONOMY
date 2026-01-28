import flet as ft
import os
from google import genai

def main(page: ft.Page):
    # --- 1. KONFIGURASI TAMPILAN (VISUAL HD) ---
    page.title = "IEA INTELLIGENCE"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#050505" # Hitam pekat
    page.padding = 0
    page.fonts = {
        "Orbitron": "https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap"
    }

    # --- 2. SETUP OTAK AI (GEMINI) ---
    # Mengambil API Key dari Environment Variable (Aman)
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else None

    # --- 3. KOMPONEN CHAT ---
    chat_list = ft.ListView(
        expand=True,
        spacing=15,
        padding=20,
        auto_scroll=True
    )

    # Fungsi untuk mengirim pesan
    def send_message(e):
        if not chat_input.value: return
        
        user_text = chat_input.value
        chat_input.value = ""
        chat_input.focus()
        
        # 3a. Munculkan Chat User (Warna Oranye)
        chat_list.controls.append(
            ft.Container(
                content=ft.Text(user_text, color="white", size=15),
                alignment=ft.alignment.center_right,
                bgcolor="#f97316", # Orange IEA
                padding=15,
                border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_left=15),
                animate_opacity=300,
            )
        )
        page.update()

        # 3b. Proses AI
        if client:
            try:
                # Animasi "Thinking..."
                loading = ft.Text("Menganalisis...", color="#666", italic=True, size=12)
                chat_list.controls.append(loading)
                page.update()

                # Panggil Gemini
                response = client.models.generate_content(
                    model="gemini-1.5-flash-latest",
                    contents=[user_text]
                )
                
                # Hapus loading, ganti jawaban AI (Warna Ungu Gelap)
                chat_list.controls.remove(loading)
                chat_list.controls.append(
                    ft.Container(
                        content=ft.Markdown(
                            response.text, 
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                        ),
                        alignment=ft.alignment.center_left,
                        bgcolor="#1a1a2e", # Deep Purple
                        padding=15,
                        border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_right=15),
                        border=ft.border.all(1, "rgba(168, 85, 247, 0.3)"), # Border Ungu Tipis
                    )
                )
            except Exception as ex:
                chat_list.controls.append(ft.Text(f"Error: {str(ex)}", color="red"))
        else:
             chat_list.controls.append(ft.Text("⚠️ API Key belum dipasang di Settings!", color="red"))

        page.update()

    # --- 4. HEADER & INPUT ---
    header = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.AUTO_AWESOME, color="#a855f7"),
            ft.Text("IEA INTELLIGENCE", font_family="Orbitron", size=20, weight="bold", color="white"),
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=20,
        bgcolor="rgba(20, 20, 30, 0.9)", # Efek Kaca
        border=ft.border.only(bottom=ft.border.BorderSide(1, "#333"))
    )

    chat_input = ft.TextField(
        hint_text="Perintahkan sistem...",
        hint_style=ft.TextStyle(color="#555"),
        border_radius=25,
        bgcolor="#111",
        border_color="#333",
        text_style=ft.TextStyle(color="white"),
        expand=True,
        on_submit=send_message
    )

    # --- 5. SUSUN HALAMAN ---
    page.add(
        header,
        ft.Container(content=chat_list, expand=True, bgcolor="#050505"), # Area Chat
        ft.Container(
            content=ft.Row([
                chat_input,
                ft.IconButton(ft.icons.SEND_ROUNDED, icon_color="#a855f7", on_click=send_message)
            ]),
            padding=20,
            bgcolor="#0a0a0f"
        )
    )

# --- 6. PENTING UNTUK DOCKER/HUGGING FACE ---
if __name__ == "__main__":
    # Baca port dari sistem, default ke 7860
    port = int(os.getenv("PORT", 7860))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")
