# from DrissionPage import ChromiumPage, ChromiumOptions
# import time
# import os
# import json
# import re


# def extract_and_open_qualified_products(page):
#     """
#     Extracts products, filters by location (CN) and experience (>1 yr),
#     and opens qualified ones in new tabs.
#     """
#     qualified_products = []
#     # Identify the cards
#     cards = page.eles("@class:gallery-card")

#     for card in cards:
#         try:
#             # 1. Extract Experience and Location
#             year_container = card.ele(".searchx-product-e-supplier__year")
#             if not year_container:
#                 continue

#             # Get year text (e.g., "5 yrs") and parse to int
#             exp_text = year_container.ele("tag:span").text
#             exp_match = re.search(r"(\d+)", exp_text)
#             experience_years = int(exp_match.group(1)) if exp_match else 0

#             # Get country code from flag image alt
#             flag_img = year_container.ele(".searchx-product-year-flag")
#             location_code = flag_img.attr("alt") if flag_img else ""

#             # 2. Apply Filters: China (CN) and > 1 year
#             if location_code == "CN" and experience_years > 1:
#                 # 3. Extract rest of the details for logging
#                 title = card.ele(".searchx-product-e-title").text

#                 # 4. Open in new tab
#                 # We find the clickable link and use DrissionPage's 'for_new_tab' logic
#                 link_ele = card.ele(".searchx-product-e-slider__link")
#                 if link_ele:
#                     new_tab = link_ele.click.for_new_tab()
#                     print(
#                         f"Qualified: {title} | Exp: {experience_years}yr | Status: Opened Tab"
#                     )

#                     # Optional: Switch back to the search page if needed
#                     # page.to_tab(page.tab_ids[0])

#                     qualified_products.append(
#                         {
#                             "title": title,
#                             "experience": experience_years,
#                             "location": "China",
#                             "tab_id": new_tab.id,
#                         }
#                     )

#         except Exception as e:
#             print(f"Error processing card: {e}")
#             continue

#     return qualified_products


# def extract_product_details(page):
#     products = []
#     cards = page.eles("@class:gallery-card")

#     for card in cards:
#         try:
#             data = {}

#             # 1. Product Title
#             title_ele = card.ele(".searchx-product-e-title")
#             data["title"] = title_ele.text if title_ele else "N/A"

#             # 2. Supplier Name
#             supplier_ele = card.ele(".searchx-product-e-company")
#             data["supplier_name"] = supplier_ele.text if supplier_ele else "N/A"

#             # 3. Experience & Location (Targeting your specific snippet)
#             # Find the container with the 'yrs' text
#             year_container = card.ele(".searchx-product-e-supplier__year")

#             if year_container:
#                 # Extracts '5 yrs'
#                 data["experience"] = year_container.ele("tag:span").text

#                 # Extracts 'CN' from the image alt attribute
#                 flag_img = year_container.ele(".searchx-product-year-flag")
#                 data["location_code"] = flag_img.attr("alt") if flag_img else "N/A"

#                 # Mapping the code to a full name if you prefer
#                 if data["location_code"] == "CN":
#                     data["location_full"] = "China"
#                 else:
#                     data["location_full"] = data["location_code"]
#             else:
#                 data["experience"] = "N/A"
#                 data["location_code"] = "N/A"

#             # 4. Price & MOQ
#             price_ele = card.ele(".searchx-product-price-price-main")
#             data["price"] = price_ele.text if price_ele else "N/A"

#             moq_ele = card.ele(".searchx-moq")
#             data["moq"] = moq_ele.text if moq_ele else "N/A"

#             products.append(data)

#         except Exception as e:
#             print(f"Error extracting card: {e}")
#             continue

#     return products


# def _apply_supplier_features_filters(page):
#     """
#     Applies both 'Verified Supplier' and 'Verified Pro Supplier' filters
#     using their unique IDs from the HTML provided.
#     """
#     filters_to_click = [
#         "assessmentCompany-ASS",  # Verified Supplier
#         "verifiedPro-verified_pro",  # Verified Pro Supplier
#     ]

#     for filter_id in filters_to_click:
#         try:
#             # We target the label associated with the checkbox ID
#             target = page.ele(f"@for={filter_id}", timeout=5)
#             if target:
#                 parent = target.parent(".searchx-filter-interactive")
#                 is_selected = parent.attr(
#                     "data-params"
#                 ) and "filterValue=true" in parent.attr("data-params")

#                 if not is_selected:
#                     target.click()
#                     print(f"Applied filter: {filter_id}")
#                     time.sleep(3)  # Wait for AJAX update
#                 else:
#                     print(f"Filter {filter_id} is already active.")

#                 time.sleep(3)
#         except Exception as e:
#             print(f"Could not apply filter {filter_id}: {e}")


# def _dismiss_popups(page) -> None:

#     selectors = [
#         "button[aria-label='Close']",
#         ".close-icon",
#         ".close",
#         ".ui-dialog-close",
#     ]

#     for sel in selectors:

#         try:

#             btn = page.ele(sel, timeout=2)

#             if btn:

#                 btn.click()

#                 time.sleep(1)

#         except Exception:

#             continue


# def alibaba_image_search(image_path: str):
#     # 1. Setup Session
#     co = ChromiumOptions()
#     # Ensure this path is correct for your system
#     co.set_user_data_path(r"C:\Users\vinay\Downloads\Alibaba_UserProfile")
#     page = ChromiumPage(co)

#     # 2. Automated Login Sequence
#     print("Navigating to Login Page...")
#     page.get("https://login.alibaba.com/")

#     try:
#         # Input Email
#         email_input = page.ele("@name=account", timeout=10)
#         if email_input:
#             email_input.clear()
#             time.sleep(2)
#             email_input.input("10a.vinaykhedkar@gmail.com")
#             print("Email entered.")

#         # Input Password
#         pass_input = page.ele("@name=password", timeout=10)
#         if pass_input:
#             pass_input.clear()
#             time.sleep(1)
#             pass_input.input("Vinaymk@2005")
#             print("Password entered.")

#         # Click Continue/Sign In
#         login_btn = page.ele("text=Continue", timeout=5) or page.ele(
#             "button[aria-label='Continue']"
#         )
#         if login_btn:
#             time.sleep(2)
#             login_btn.click()
#             print("Login button clicked. Waiting for redirection...")

#         # Wait for redirection back to home page or search-ready state
#         page.wait.url_change("login.alibaba.com", timeout=30)
#         time.sleep(5)

#     except Exception as e:
#         print(f"Login process encountered an issue: {e}")

#     # 3. Image Search Sequence
#     try:
#         _dismiss_popups(page)

#         # Click Image Search Button as requested
#         image_search_btn = page.ele("@data-search=switch-image-upload", timeout=10)
#         if image_search_btn:
#             time.sleep(3)
#             image_search_btn.click()
#             print("Triggered image search upload.")
#             time.sleep(2)

#             # 4. Upload File
#             if not os.path.exists(image_path):
#                 print(f"ERROR: Image not found at {image_path}")
#                 return

#             file_input = page.ele(".upload-file", timeout=10)
#             if file_input:
#                 time.sleep(1)
#                 file_input.input(image_path)
#                 print(f"Uploading: {image_path}")

#                 # 5. Wait for Search Results URL change
#                 print("Waiting for search results...")
#                 page.wait.url_change("/search/page?", timeout=30)

#                 time.sleep(1.5)
#                 _apply_supplier_features_filters(page)

#                 # 6. Extract Product Details
#                 products = extract_product_details(page)

#                 print(f"Extracted {len(products)} products from search results.")

#                 # Save to JSON file
#                 output_file = os.path.join(
#                     os.path.dirname(__file__),
#                     "output",
#                     f"products_{int(time.time())}.json",
#                 )
#                 with open(output_file, "w", encoding="utf-8") as f:
#                     json.dump(products, f, indent=2, ensure_ascii=False)
#                 print(f"Saved product details to: {output_file}")


#     except Exception as e:
#         print(f"Search/Upload Error: {e}")


# if __name__ == "__main__":
#     alibaba_image_search(
#         os.path.join(os.path.dirname(__file__), "data", "uploaded_image_1770884171.png")
#     )
#     pass


from DrissionPage import ChromiumPage, ChromiumOptions
import time
import os
import json
import re


def filter_and_message_suppliers(page):
    """
    Filters for qualified suppliers (China + >1yr), opens their product pages,
    and sends the specific inquiry message provided.
    """
    qualified_count = 0
    main_tab_id = page.tab_id
    cards = page.eles("@class:gallery-card")

    inquiry_message = (
        "Hello,\n"
        "I am interested in buying 500 pcs in a pack of 50 each. "
        "Can you send the pricing for the same?"
    )

    for card in cards:
        try:
            # 1. Experience & Location Filtering
            year_container = card.ele(".searchx-product-e-supplier__year")
            if not year_container:
                continue

            exp_text = year_container.ele("tag:span").text
            exp_match = re.search(r"(\d+)", exp_text)
            experience_years = int(exp_match.group(1)) if exp_match else 0

            flag_img = year_container.ele(".searchx-product-year-flag")
            location_code = flag_img.attr("alt") if flag_img else ""

            # Check logic: Location China (CN) and Experience > 1 year
            if location_code == "CN" and experience_years > 1:
                link_ele = card.ele(".searchx-product-e-slider__link")
                if not link_ele:
                    continue

                print(f"--- Found Qualified Supplier ({experience_years} yrs) ---")

                # 2. Open Product in New Tab
                new_tab = link_ele.click.for_new_tab()

                try:
                    # 3. Handle Messaging Sequence
                    # Find the specific 'Chat now' button provided
                    chat_btn = new_tab.ele(
                        "@data-testid:wholesaleSkuSummary-CHAT", timeout=15
                    )

                    if not chat_btn:
                        chat_btn = new_tab.ele(
                            "@data-testid:customizationSkuSummary-CHAT", timeout=15
                        )

                    if chat_btn:
                        chat_btn.click()
                        time.sleep(4)  # Allow chat window to pop up

                        # Find the textarea with class 'send-textarea'
                        textbox = new_tab.ele("@class:send-textarea", timeout=10)
                        if textbox:
                            textbox.clear()
                            time.sleep(1)
                            textbox.input(inquiry_message)

                            # Find the Submit button with class 'send-tool-button'
                            send_btn = new_tab.ele("@class:send-tool-button", timeout=5)
                            if send_btn:
                                send_btn.click()
                                print(
                                    f"Successfully sent message to supplier of: {new_tab.title}"
                                )
                                qualified_count += 1
                                time.sleep(2)  # Buffer for send completion
                        else:
                            print("Could not find the chat input box.")
                    else:
                        print("Chat now button not found on product page.")

                    new_tab.close()  # Close tab to save memory

                except Exception as tab_err:
                    print(f"Error messaging this supplier: {tab_err}")
                    new_tab.close()

                # Optional: limit to avoid spam/browser lag
                if qualified_count >= 10:
                    break

        except Exception as e:
            print(f"Error processing card: {e}")
            continue

    page.to_tab(main_tab_id)  # Return to search results
    return qualified_count


# --- Original functions with minor maintenance ---


def extract_product_details(page):
    products = []
    cards = page.eles("@class:gallery-card")
    for card in cards:
        try:
            data = {}
            title_ele = card.ele(".searchx-product-e-title")
            data["title"] = title_ele.text if title_ele else "N/A"
            supplier_ele = card.ele(".searchx-product-e-company")
            data["supplier_name"] = supplier_ele.text if supplier_ele else "N/A"
            year_container = card.ele(".searchx-product-e-supplier__year")
            if year_container:
                data["experience"] = year_container.ele("tag:span").text
                flag_img = year_container.ele(".searchx-product-year-flag")
                data["location_code"] = flag_img.attr("alt") if flag_img else "N/A"
                data["location_full"] = (
                    "China" if data["location_code"] == "CN" else data["location_code"]
                )
            else:
                data["experience"] = "N/A"
                data["location_code"] = "N/A"
            price_ele = card.ele(".searchx-product-price-price-main")
            data["price"] = price_ele.text if price_ele else "N/A"
            moq_ele = card.ele(".searchx-moq")
            data["moq"] = moq_ele.text if moq_ele else "N/A"
            products.append(data)

            print(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            print(f"Error extracting card: {e}")
            continue
    return products


def _apply_supplier_features_filters(page):
    filters_to_click = ["assessmentCompany-ASS", "verifiedPro-verified_pro"]
    for filter_id in filters_to_click:
        try:
            target = page.ele(f"@for={filter_id}", timeout=5)
            if target:
                parent = target.parent(".searchx-filter-interactive")
                is_selected = parent.attr(
                    "data-params"
                ) and "filterValue=true" in parent.attr("data-params")
                if not is_selected:
                    target.click()
                    print(f"Applied filter: {filter_id}")
                    time.sleep(3)
        except Exception as e:
            print(f"Could not apply filter {filter_id}: {e}")


def _dismiss_popups(page) -> None:
    selectors = [
        "button[aria-label='Close']",
        ".close-icon",
        ".close",
        ".ui-dialog-close",
    ]
    for sel in selectors:
        try:
            btn = page.ele(sel, timeout=2)
            if btn:
                btn.click()
                time.sleep(1)
        except Exception:
            continue


def alibaba_image_search(image_path: str):
    co = ChromiumOptions()
    co.set_user_data_path(r"C:\Users\vinay\Downloads\Alibaba_UserProfile")
    page = ChromiumPage(co)

    print("Navigating to Login Page...")
    page.get("https://login.alibaba.com/")

    try:
        email_input = page.ele("@name=account", timeout=10)
        if email_input:
            email_input.clear()
            email_input.input("10a.vinaykhedkar@gmail.com")
        pass_input = page.ele("@name=password", timeout=10)
        if pass_input:
            pass_input.clear()
            pass_input.input("Vinaymk@2005")
        login_btn = page.ele("text=Continue", timeout=5) or page.ele(
            "button[aria-label='Continue']"
        )
        if login_btn:
            login_btn.click()
        page.wait.url_change("login.alibaba.com", timeout=30)
        time.sleep(5)
    except Exception as e:
        print(f"Login process issue: {e}")

    try:
        _dismiss_popups(page)
        image_search_btn = page.ele("@data-search=switch-image-upload", timeout=10)
        if image_search_btn:
            time.sleep(2)
            image_search_btn.click()
            time.sleep(2)
            if not os.path.exists(image_path):
                print(f"ERROR: Image not found at {image_path}")
                return
            file_input = page.ele(".upload-file", timeout=10)
            if file_input:
                file_input.input(image_path)
                print(f"Uploading: {image_path}")
                page.wait.url_change("/search/page?", timeout=30)
                time.sleep(3)

                _apply_supplier_features_filters(page)

                # Logic implementation: Message qualified suppliers
                print("Starting filtering and messaging sequence...")
                total_sent = filter_and_message_suppliers(page)
                print(f"Finished! Total messages sent: {total_sent}")

                # Optional: Still extract data for local JSON record
                products = extract_product_details(page)
                print(f"Extraction complete for {len(products)} items.")

    except Exception as e:
        print(f"Search/Upload Error: {e}")


if __name__ == "__main__":
    img = os.path.join(
        os.path.dirname(__file__), "data", "uploaded_image_1771097717.png"
    )
    alibaba_image_search(img)
