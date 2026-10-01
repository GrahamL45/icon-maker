#include <Geode/Geode.hpp>
#include <Geode/modify/MenuLayer.hpp>

#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <string>

using namespace geode::prelude;

namespace {

constexpr float kIconSize = 64.f;
constexpr unsigned int kFrameCount = 5;

ccColor4F toColor4F(ccColor3B color, float alpha = 1.f) {
	return {
		static_cast<float>(color.r) / 255.f,
		static_cast<float>(color.g) / 255.f,
		static_cast<float>(color.b) / 255.f,
		alpha
	};
}

void drawIconPart(CCNode* parent, int part, const std::array<ccColor3B, 4>& colors, float x) {
	auto node = CCDrawNode::create();
	node->setPosition({x, kIconSize / 2.f});
	parent->addChild(node);

	CCPoint body[] = {
		{-23.f, -20.f}, {23.f, -20.f}, {27.f, 7.f}, {0.f, 25.f}, {-27.f, 7.f}
	};
	CCPoint secondary[] = {
		{-18.f, -12.f}, {12.f, -12.f}, {19.f, 6.f}, {-1.f, 16.f}, {-19.f, 5.f}
	};
	CCPoint detailLeft[] = {
		{-13.f, 3.f}, {-5.f, 3.f}, {-5.f, 11.f}, {-13.f, 11.f}
	};
	CCPoint detailRight[] = {
		{5.f, 3.f}, {13.f, 3.f}, {13.f, 11.f}, {5.f, 11.f}
	};

	auto outline = toColor4F({20, 20, 30});
	if (part == 0 || part == 4) {
		node->drawPolygon(body, 5, toColor4F(colors[0]), 2.f, outline);
	}
	if (part == 1 || part == 4) {
		node->drawPolygon(secondary, 5, toColor4F(colors[1]), 1.f, outline);
	}
	if (part == 2 || part == 4) {
		node->drawPolygon(body, 5, {0.f, 0.f, 0.f, 0.f}, 5.f, toColor4F(colors[2], .9f));
	}
	if (part == 3 || part == 4) {
		node->drawPolygon(detailLeft, 4, toColor4F(colors[3]), 0.f, toColor4F(colors[3]));
		node->drawPolygon(detailRight, 4, toColor4F(colors[3]), 0.f, toColor4F(colors[3]));
	}
}

std::string makePlist() {
	static constexpr std::array<const char*, kFrameCount> names = {
		"base.png", "secondary.png", "glow.png", "detail.png", "icon.png"
	};
	std::string plist =
		"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
		"<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
		"\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
		"<plist version=\"1.0\"><dict><key>frames</key><dict>\n";

	for (unsigned int i = 0; i < names.size(); ++i) {
		plist += "<key>" + std::string(names[i]) + "</key><dict>"
			"<key>frame</key><string>{{" + std::to_string(i * 64) +
			",0},{64,64}}</string><key>offset</key><string>{0,0}</string>"
			"<key>rotated</key><false/><key>sourceColorRect</key>"
			"<string>{{0,0},{64,64}}</string><key>sourceSize</key>"
			"<string>{64,64}</string></dict>\n";
	}

	plist +=
		"</dict><key>metadata</key><dict><key>format</key><integer>3</integer>"
		"<key>pixelFormat</key><string>RGBA8888</string>"
		"<key>realTextureFileName</key><string>icon-maker.png</string>"
		"<key>size</key><string>{320,64}</string>"
		"<key>textureFileName</key><string>icon-maker.png</string>"
		"</dict></dict></plist>\n";
	return plist;
}

class IconMakerPopup final : public Popup {
protected:
	std::array<ccColor3B, 4> m_colors{{
		{65, 170, 255}, {255, 205, 55}, {255, 110, 210}, {25, 30, 45}
	}};
	std::array<CCLayerColor*, 4> m_swatches{};
	std::array<CCMenuItemLabel*, 4> m_layerButtons{};
	CCNode* m_preview = nullptr;
	int m_selectedLayer = 0;

	bool init() {
		if (!Popup::init(440.f, 300.f)) {
			return false;
		}

		this->setTitle("Icon Maker");

		auto menu = CCMenu::create();
		menu->setPosition({0.f, 0.f});
		this->addChild(menu);

		static constexpr std::array<const char*, 4> layerNames = {
			"Base", "Secondary", "Glow", "Detail"
		};
		for (int i = 0; i < 4; ++i) {
			float y = 73.f - static_cast<float>(i) * 43.f;
			auto label = CCLabelBMFont::create(layerNames[i], "bigFont.fnt");
			label->setScale(.42f);
			auto button = CCMenuItemLabel::create(
				label, this, menu_selector(IconMakerPopup::onSelectLayer)
			);
			button->setTag(i);
			button->setPosition({-151.f, y});
			menu->addChild(button);
			m_layerButtons[i] = button;

			auto swatch = CCLayerColor::create(
				{m_colors[i].r, m_colors[i].g, m_colors[i].b, 255}, 18.f, 18.f
			);
			swatch->setPosition({-119.f, y - 9.f});
			this->addChild(swatch);
			m_swatches[i] = swatch;
		}

		addColorButton(menu, "R-", -78.f, 73.f, menu_selector(IconMakerPopup::onRedDown));
		addColorButton(menu, "R+", -48.f, 73.f, menu_selector(IconMakerPopup::onRedUp));
		addColorButton(menu, "G-", -78.f, 30.f, menu_selector(IconMakerPopup::onGreenDown));
		addColorButton(menu, "G+", -48.f, 30.f, menu_selector(IconMakerPopup::onGreenUp));
		addColorButton(menu, "B-", -78.f, -13.f, menu_selector(IconMakerPopup::onBlueDown));
		addColorButton(menu, "B+", -48.f, -13.f, menu_selector(IconMakerPopup::onBlueUp));

		auto previewBack = CCLayerColor::create({35, 38, 52, 255}, 112.f, 112.f);
		previewBack->setPosition({24.f, -2.f});
		this->addChild(previewBack);

		m_preview = CCNode::create();
		m_preview->setPosition({80.f, 54.f});
		this->addChild(m_preview);

		addColorButton(menu, "Export PNG + PLIST", 80.f, -77.f, menu_selector(IconMakerPopup::onExport));
		refresh();
		return true;
	}

	void addColorButton(
		CCMenu* menu, const char* text, float x, float y, SEL_MenuHandler handler
	) {
		auto label = CCLabelBMFont::create(text, "bigFont.fnt");
		label->setScale(.38f);
		auto button = CCMenuItemLabel::create(label, this, handler);
		button->setPosition({x, y});
		menu->addChild(button);
	}

	void refresh() {
		for (int i = 0; i < 4; ++i) {
			auto color = m_colors[i];
			m_swatches[i]->setColor(color);
			m_layerButtons[i]->setColor(i == m_selectedLayer ? ccColor3B{255, 230, 70} : ccColor3B{255, 255, 255});
		}

		m_preview->removeAllChildrenWithCleanup(true);
		drawIconPart(m_preview, 4, m_colors, 0.f);
	}

	void adjust(int channel, int amount) {
		auto& color = m_colors[m_selectedLayer];
		GLubyte* channels[] = {&color.r, &color.g, &color.b};
		*channels[channel] = static_cast<GLubyte>(
			std::clamp(static_cast<int>(*channels[channel]) + amount, 0, 255)
		);
		refresh();
	}

	void onSelectLayer(CCObject* sender) {
		m_selectedLayer = sender->getTag();
		refresh();
	}

	void onRedDown(CCObject*) { adjust(0, -16); }
	void onRedUp(CCObject*) { adjust(0, 16); }
	void onGreenDown(CCObject*) { adjust(1, -16); }
	void onGreenUp(CCObject*) { adjust(1, 16); }
	void onBlueDown(CCObject*) { adjust(2, -16); }
	void onBlueUp(CCObject*) { adjust(2, 16); }

	void onExport(CCObject*) {
		auto outputDir = Mod::get()->getSaveDir();
		std::error_code filesystemError;
		std::filesystem::create_directories(outputDir, filesystemError);
		if (filesystemError) {
			FLAlertLayer::create(
				"Icon Maker", "Could not create the export folder:\n" + filesystemError.message(), "OK"
			)->show();
			return;
		}
		auto pngPath = outputDir / "icon-maker.png";
		auto plistPath = outputDir / "icon-maker.plist";

		auto renderTexture = CCRenderTexture::create(
			static_cast<int>(kIconSize * kFrameCount),
			static_cast<int>(kIconSize),
			kCCTexture2DPixelFormat_RGBA8888
		);
		if (!renderTexture) {
			FLAlertLayer::create("Icon Maker", "Could not create the export canvas.", "OK")->show();
			return;
		}

		auto sheet = CCNode::create();
		for (int i = 0; i < 4; ++i) {
			drawIconPart(sheet, i, m_colors, kIconSize * (i + .5f));
		}
		drawIconPart(sheet, 4, m_colors, kIconSize * 4.5f);

		renderTexture->beginWithClear(0.f, 0.f, 0.f, 0.f);
		sheet->visit();
		renderTexture->end();

		auto image = renderTexture->newCCImage(true);
		if (!image) {
			FLAlertLayer::create("Icon Maker", "Could not encode the icon sheet.", "OK")->show();
			return;
		}
		auto pngSaved = image->saveToFile(pngPath.string().c_str(), false);
		delete image;
		if (!pngSaved) {
			FLAlertLayer::create("Icon Maker", "Could not write icon-maker.png.", "OK")->show();
			return;
		}

		std::ofstream plist(plistPath, std::ios::binary);
		if (!plist) {
			FLAlertLayer::create("Icon Maker", "Could not write icon-maker.plist.", "OK")->show();
			return;
		}
		plist << makePlist();
		plist.close();
		if (!plist) {
			FLAlertLayer::create("Icon Maker", "The plist could not be saved completely.", "OK")->show();
			return;
		}

		FLAlertLayer::create(
			"Icon Maker",
			"Exported icon-maker.png and icon-maker.plist to:\n" + outputDir.string(),
			"OK"
		)->show();
	}

public:
	static IconMakerPopup* create() {
		auto popup = new IconMakerPopup();
		if (popup && popup->init()) {
			popup->autorelease();
			return popup;
		}
		CC_SAFE_DELETE(popup);
		return nullptr;
	}
};

}

class $modify(IconMakerMenuLayer, MenuLayer) {
	bool init() {
		if (!MenuLayer::init()) {
			return false;
		}

		auto menu = this->getChildByID("bottom-menu");
		if (!menu) {
			return true;
		}

		auto label = CCLabelBMFont::create("ICON", "bigFont.fnt");
		label->setScale(.55f);
		auto button = CCMenuItemLabel::create(
			label, this, menu_selector(IconMakerMenuLayer::onOpenIconMaker)
		);
		menu->addChild(button);
		menu->updateLayout();
		return true;
	}

	void onOpenIconMaker(CCObject*) {
		if (auto popup = IconMakerPopup::create()) {
			popup->show();
		}
	}
};
