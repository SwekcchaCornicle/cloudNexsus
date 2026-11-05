from app.services.html_extractor import extract_html


def test_extractor_removes_navigation_and_preserves_heading():
    html = '''
    <html><head><title>Sample</title></head><body>
      <nav>Home Pricing Login</nav>
      <main>
        <h1>Cloud Functions</h1>
        <h2>Overview</h2>
        <p>Runs code in response to events.</p>
        <pre>def handler(event): return True</pre>
      </main>
      <footer>Copyright footer</footer>
    </body></html>
    '''
    title, blocks = extract_html(html)
    assert title == "Sample"
    assert all("Home Pricing" not in block.text for block in blocks)
    assert all("Copyright footer" not in block.text for block in blocks)
    assert blocks[0].heading_path == ["Cloud Functions", "Overview"]
    assert any(block.block_type == "code" for block in blocks)
