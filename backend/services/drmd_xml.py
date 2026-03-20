"""Utilities for generating DRMD XML and scoring against a master XML."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any


CAS_DATABASE: dict[str, str] = {
    "h": "1333-74-0",
    "hydrogen": "1333-74-0",
    "he": "7440-59-7",
    "helium": "7440-59-7",
    "li": "7439-93-2",
    "lithium": "7439-93-2",
    "be": "7440-41-7",
    "beryllium": "7440-41-7",
    "b": "7440-42-8",
    "boron": "7440-42-8",
    "c": "7440-44-0",
    "carbon": "7440-44-0",
    "n": "7727-37-9",
    "nitrogen": "7727-37-9",
    "o": "7782-44-7",
    "oxygen": "7782-44-7",
    "na": "7440-23-5",
    "sodium": "7440-23-5",
    "mg": "7439-95-4",
    "magnesium": "7439-95-4",
    "al": "7429-90-5",
    "aluminum": "7429-90-5",
    "aluminium": "7429-90-5",
    "si": "7440-21-3",
    "silicon": "7440-21-3",
    "p": "7723-14-0",
    "phosphorus": "7723-14-0",
    "s": "7704-34-9",
    "sulfur": "7704-34-9",
    "cl": "7782-50-5",
    "chlorine": "7782-50-5",
    "k": "7440-09-7",
    "potassium": "7440-09-7",
    "ca": "7440-70-2",
    "calcium": "7440-70-2",
    "ti": "7440-32-6",
    "titanium": "7440-32-6",
    "v": "7440-62-2",
    "vanadium": "7440-62-2",
    "cr": "7440-47-3",
    "chromium": "7440-47-3",
    "mn": "7439-96-5",
    "manganese": "7439-96-5",
    "fe": "7439-89-6",
    "iron": "7439-89-6",
    "co": "7440-48-4",
    "cobalt": "7440-48-4",
    "ni": "7440-02-0",
    "nickel": "7440-02-0",
    "cu": "7440-50-8",
    "copper": "7440-50-8",
    "zn": "7440-66-6",
    "zinc": "7440-66-6",
    "ga": "7440-55-3",
    "gallium": "7440-55-3",
    "ge": "7440-56-4",
    "germanium": "7440-56-4",
    "as": "7440-38-2",
    "arsenic": "7440-38-2",
    "se": "7782-49-2",
    "selenium": "7782-49-2",
    "br": "7726-95-6",
    "bromine": "7726-95-6",
    "rb": "7440-17-7",
    "rubidium": "7440-17-7",
    "sr": "7440-24-6",
    "strontium": "7440-24-6",
    "y": "7440-65-5",
    "yttrium": "7440-65-5",
    "zr": "7440-67-7",
    "zirconium": "7440-67-7",
    "nb": "7440-03-1",
    "niobium": "7440-03-1",
    "mo": "7439-98-7",
    "molybdenum": "7439-98-7",
    "ag": "7440-22-4",
    "silver": "7440-22-4",
    "cd": "7440-43-9",
    "cadmium": "7440-43-9",
    "sn": "7440-31-5",
    "tin": "7440-31-5",
    "sb": "7440-36-0",
    "antimony": "7440-36-0",
    "i": "7553-56-2",
    "iodine": "7553-56-2",
    "ba": "7440-39-3",
    "barium": "7440-39-3",
    "pt": "7440-06-4",
    "platinum": "7440-06-4",
    "au": "7440-57-5",
    "gold": "7440-57-5",
    "hg": "7439-97-6",
    "mercury": "7439-97-6",
    "pb": "7439-92-1",
    "lead": "7439-92-1",
    "bi": "7440-69-9",
    "bismuth": "7440-69-9",
    "u": "7440-61-1",
    "uranium": "7440-61-1",
}

UNIT_MAP: dict[str, tuple[str, float]] = {
    "%": ("\\percent", 1.0),
    "percent": ("\\percent", 1.0),
    "ppm": ("\\one", 1e-6),
    "ppb": ("\\one", 1e-9),
    "one": ("\\one", 1.0),
    "mg/kg": ("\\milli\\gram\\kilogram\\tothe{-1}", 1.0),
    "mgkg-1": ("\\milli\\gram\\kilogram\\tothe{-1}", 1.0),
    "ug/kg": ("\\micro\\gram\\kilogram\\tothe{-1}", 1.0),
    "µg/kg": ("\\micro\\gram\\kilogram\\tothe{-1}", 1.0),
    "μg/kg": ("\\micro\\gram\\kilogram\\tothe{-1}", 1.0),
    "g/kg": ("\\gram\\kilogram\\tothe{-1}", 1.0),
    "mg/g": ("\\milli\\gram\\gram\\tothe{-1}", 1.0),
    "ug/g": ("\\micro\\gram\\gram\\tothe{-1}", 1.0),
    "µg/g": ("\\micro\\gram\\gram\\tothe{-1}", 1.0),
    "μg/g": ("\\micro\\gram\\gram\\tothe{-1}", 1.0),
    "m2/g": ("\\metre\\tothe{2}\\gram\\tothe{-1}", 1.0),
    "m²/g": ("\\metre\\tothe{2}\\gram\\tothe{-1}", 1.0),
    "cm2/g": ("\\centi\\metre\\tothe{2}\\gram\\tothe{-1}", 1.0),
    "cm²/g": ("\\centi\\metre\\tothe{2}\\gram\\tothe{-1}", 1.0),
    "mg": ("\\milli\\gram", 1.0),
    "g": ("\\gram", 1.0),
    "kg": ("\\kilogram", 1.0),
    "ug": ("\\micro\\gram", 1.0),
    "µg": ("\\micro\\gram", 1.0),
    "μg": ("\\micro\\gram", 1.0),
    "lb": ("\\kilogram", 0.45359237),
    "oz": ("\\kilogram", 0.02834959),
    "nm": ("\\nano\\metre", 1.0),
    "um": ("\\micro\\metre", 1.0),
    "µm": ("\\micro\\metre", 1.0),
    "μm": ("\\micro\\metre", 1.0),
    "mm": ("\\milli\\metre", 1.0),
    "cm": ("\\centi\\metre", 1.0),
    "m": ("\\metre", 1.0),
    "km": ("\\kilo\\metre", 1.0),
    "m2": ("\\metre\\tothe{2}", 1.0),
    "m²": ("\\metre\\tothe{2}", 1.0),
    "cm2": ("\\centi\\metre\\tothe{2}", 1.0),
    "cm²": ("\\centi\\metre\\tothe{2}", 1.0),
    "g/cm3": ("\\gram\\centi\\metre\\tothe{-3}", 1.0),
    "g/cm³": ("\\gram\\centi\\metre\\tothe{-3}", 1.0),
    "c": ("\\degreecelsius", 1.0),
    "°c": ("\\degreecelsius", 1.0),
    "k": ("\\kelvin", 1.0),
    "h": ("\\hour", 1.0),
    "min": ("\\minute", 1.0),
    "s": ("\\second", 1.0),
    "l": ("\\litre", 1.0),
    "ml": ("\\milli\\litre", 1.0),
    "pa": ("\\pascal", 1.0),
    "bar": ("\\pascal", 100000.0),
    "mbar": ("\\pascal", 100.0),
    "hpa": ("\\pascal", 100.0),
}


def _num_str(text: str) -> str:
    return re.sub(r"[^0-9.eE+-]", "", text)


def _normalize_unit_key(unit: str) -> str:
    key = re.sub(r"^\s*in\s+", "", str(unit).strip(), flags=re.IGNORECASE)
    key = re.sub(r"\s+", "", key)
    key = (
        key.replace("⁻", "-")
        .replace("¹", "1")
        .replace("²", "2")
        .replace("³", "3")
    )
    return key.lower()


def convert_to_dsi(value: Any, unit: Any) -> tuple[str, str]:
    raw_value = "" if value is None else str(value).strip()
    raw_unit = "" if unit is None else str(unit).strip()
    if not raw_unit:
        return raw_value, ""

    if raw_unit.startswith("\\"):
        return raw_value, raw_unit

    key = _normalize_unit_key(raw_unit)
    conversion = UNIT_MAP.get(key)
    if not conversion:
        return raw_value, raw_unit

    dsi_unit, factor = conversion
    try:
        number = float(_num_str(raw_value))
        converted = number * factor
        dsi_value = str(float(f"{converted:.10g}")) if factor != 1.0 else raw_value
        return dsi_value, dsi_unit
    except ValueError:
        return raw_value, dsi_unit


def get_cas_number(name_or_symbol: str | None) -> str | None:
    if not name_or_symbol:
        return None
    key = name_or_symbol.strip().lower()
    if key in CAS_DATABASE:
        return CAS_DATABASE[key]

    parts = re.split(r"[^a-zA-Z]+", key)
    for part in parts:
        if part and part in CAS_DATABASE:
            return CAS_DATABASE[part]
    return None


def escape_xml(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("'", "&apos;")
        .replace('"', "&quot;")
    )


def _render_validity(admin: dict[str, Any]) -> str:
    validity_type = admin.get("validityType")
    if validity_type == "Until Revoked":
        return "        <drmd:untilRevoked>true</drmd:untilRevoked>"
    if validity_type == "Specific Time":
        return (
            "        <drmd:specificTime>"
            f"{escape_xml(admin.get('specificTime', ''))}"
            "</drmd:specificTime>"
        )
    if validity_type == "Time After Dispatch":
        duration_y = int(admin.get("durationY") or 0)
        duration_m = int(admin.get("durationM") or 0)

        # Normalize overflow months so 12M -> P1Y and 13M -> P1Y1M.
        duration_y += duration_m // 12
        duration_m = duration_m % 12

        iso = "P"
        if duration_y:
            iso += f"{duration_y}Y"
        if duration_m:
            iso += f"{duration_m}M"
        if iso == "P":
            iso = "P0Y"
        return (
            "        <drmd:timeAfterDispatch>\n"
            f"          <drmd:dispatchDate>{escape_xml(admin.get('dateOfIssue', ''))}</drmd:dispatchDate>\n"
            f"          <drmd:period>{escape_xml(iso)}</drmd:period>\n"
            "        </drmd:timeAfterDispatch>"
        )
    return ""


def _render_primitive_quantity(value: str) -> str:
    if not value or value == "noQuantity":
        return (
            "\n          <drmd:noQuantity>\n"
            "            <dcc:content>noQuantity</dcc:content>\n"
            "          </drmd:noQuantity>"
        )

    regex = r"^([\d.]+(?:[eE][+-]?\d+)?)\s*(\S.*)$"
    match = re.match(regex, value.strip())
    if match:
        return (
            "\n          <drmd:real>\n"
            f"            <si:value>{escape_xml(match.group(1))}</si:value>\n"
            f"            <si:unit>{escape_xml(match.group(2))}</si:unit>\n"
            "          </drmd:real>"
        )

    return (
        "\n          <drmd:noQuantity>\n"
        f"            <dcc:content>{escape_xml(value)}</dcc:content>\n"
        "          </drmd:noQuantity>"
    )


def _normalize_xml_for_compare(xml_text: str) -> dict[str, str]:
    root = ET.fromstring(xml_text)
    values: dict[str, str] = {}

    def walk(elem: ET.Element, path: str) -> None:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        current_path = f"{path}/{tag}" if path else tag

        for attr_key, attr_val in sorted(elem.attrib.items()):
            values[f"{current_path}@{attr_key}"] = " ".join(attr_val.split())

        text = (elem.text or "").strip()
        if text:
            values[current_path] = " ".join(text.split())

        # Keep sibling indexes to avoid collisions for repeated tags.
        child_counts: dict[str, int] = {}
        for child in elem:
            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            idx = child_counts.get(child_tag, 0)
            child_counts[child_tag] = idx + 1
            walk(child, f"{current_path}[{idx}]")

    walk(root, "")

    filtered: dict[str, str] = {}
    for k, v in values.items():
        # Ignore random identifiers for fair comparison.
        if "/uniqueIdentifier" in k:
            continue
        # Ignore embedded binary document payload blocks.
        if "/document" in k:
            continue
        # Ignore dispatch date in validity comparison.
        if "/validity" in k and "/dispatchDate" in k:
            continue
        # Ignore signer flags in comparison.
        if "/mainSigner" in k:
            continue
        filtered[k] = v

    # Normalize units and values to DSI for robust matching.
    normalized = dict(filtered)
    for key, unit_val in list(filtered.items()):
        if not key.endswith("/unit"):
            continue
        value_key = key[: -len("/unit")] + "/value"
        if value_key not in filtered:
            continue
        dsi_value, dsi_unit = convert_to_dsi(filtered[value_key], unit_val)
        normalized[value_key] = dsi_value
        normalized[key] = dsi_unit

    return normalized


def compare_with_master(predicted_xml: str, master_xml: str) -> dict[str, Any]:
    """
    Compare predicted XML against a master XML and score each master datapoint.
    A datapoint is a leaf text value or attribute value path.
    """
    pred_points = _normalize_xml_for_compare(predicted_xml)
    master_points = _normalize_xml_for_compare(master_xml)

    total = len(master_points)
    correct = 0
    wrong = 0

    for key, master_val in master_points.items():
        if pred_points.get(key) == master_val:
            correct += 1
        else:
            wrong += 1

    accuracy = round((correct / total) * 100, 2) if total else 0.0
    missing = sum(1 for k in master_points if k not in pred_points)
    extra = sum(1 for k in pred_points if k not in master_points)

    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "accuracy_pct": accuracy,
        "missing": missing,
        "extra": extra,
    }


def generate_drmd_xml(data: dict[str, Any]) -> str:
    administrative_data = data.get("administrativeData", {})
    materials = data.get("materials", [])
    properties = data.get("properties", [])
    statements = data.get("statements", {}).get("official", {})

    header = (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        "<drmd:digitalReferenceMaterialDocument "
        "xmlns:dcc=\"https://ptb.de/dcc\" "
        "xmlns:drmd=\"https://example.org/drmd\" "
        "xmlns:si=\"https://ptb.de/si\" "
        "schemaVersion=\"0.3.0\">"
    )

    admin_xml = (
        "\n  <drmd:administrativeData>\n"
        "    <drmd:coreData>\n"
        "      <drmd:titleOfTheDocument>referenceMaterialCertificate</drmd:titleOfTheDocument>\n"
        f"      <drmd:uniqueIdentifier>{escape_xml(administrative_data.get('uniqueIdentifier', ''))}</drmd:uniqueIdentifier>\n"
        "      <drmd:validity>\n"
        f"{_render_validity(administrative_data)}\n"
        "      </drmd:validity>\n"
        "    </drmd:coreData>"
    )

    for producer in administrative_data.get("producers", []):
        address = producer.get("address", {})
        admin_xml += (
            "\n    <drmd:referenceMaterialProducer>\n"
            "      <drmd:name>\n"
            f"        <dcc:content>{escape_xml(producer.get('name', ''))}</dcc:content>\n"
            "      </drmd:name>\n"
            "      <drmd:contact>\n"
            "        <dcc:name>\n"
            f"          <dcc:content>{escape_xml(producer.get('name', ''))}</dcc:content>\n"
            "        </dcc:name>\n"
            f"        <dcc:eMail>{escape_xml(producer.get('email', ''))}</dcc:eMail>\n"
            f"        <dcc:phone>{escape_xml(producer.get('phone', ''))}</dcc:phone>\n"
            + (
                f"        <dcc:fax>{escape_xml(producer.get('fax', ''))}</dcc:fax>\n"
                if producer.get("fax")
                else ""
            )
            + "        <dcc:location>\n"
            f"          <dcc:street>{escape_xml(address.get('street', ''))}</dcc:street>\n"
            f"          <dcc:streetNo>{escape_xml(address.get('streetNo', ''))}</dcc:streetNo>\n"
            f"          <dcc:postCode>{escape_xml(address.get('postCode', ''))}</dcc:postCode>\n"
            f"          <dcc:city>{escape_xml(address.get('city', ''))}</dcc:city>\n"
            f"          <dcc:countryCode>{escape_xml(address.get('countryCode', ''))}</dcc:countryCode>\n"
            "        </dcc:location>\n"
            "      </drmd:contact>\n"
            "    </drmd:referenceMaterialProducer>"
        )

    persons = administrative_data.get("responsiblePersons", [])
    if persons:
        admin_xml += "\n    <drmd:respPersons>"
        for person in persons:
            admin_xml += (
                "\n      <dcc:respPerson>\n"
                "        <dcc:person>\n"
                "          <dcc:name>\n"
                f"            <dcc:content>{escape_xml(person.get('name', ''))}</dcc:content>\n"
                "          </dcc:name>\n"
                "        </dcc:person>"
            )
            if person.get("description"):
                admin_xml += (
                    "\n        <dcc:description>\n"
                    f"          <dcc:content>{escape_xml(person.get('description', ''))}</dcc:content>\n"
                    "        </dcc:description>"
                )
            admin_xml += (
                f"\n        <dcc:role>{escape_xml(person.get('role', ''))}</dcc:role>\n"
                f"        <dcc:mainSigner>{str(bool(person.get('mainSigner', False))).lower()}</dcc:mainSigner>\n"
                "      </dcc:respPerson>"
            )
        admin_xml += "\n    </drmd:respPersons>"

    admin_xml += "\n  </drmd:administrativeData>"

    materials_xml = "\n  <drmd:materials>"
    for material in materials:
        materials_xml += (
            "\n    <drmd:material>\n"
            "      <drmd:name>\n"
            f"        <dcc:content>{escape_xml(material.get('name', ''))}</dcc:content>\n"
            "      </drmd:name>\n"
            "      <drmd:description>\n"
            f"        <dcc:content>{escape_xml(material.get('description', ''))}</dcc:content>\n"
            "      </drmd:description>"
        )

        identifiers = [
            i
            for i in material.get("materialIdentifiers", [])
            if str(i.get("value", "")).strip()
        ]
        if identifiers:
            materials_xml += "\n      <drmd:materialIdentifiers>"
            for identifier in identifiers:
                materials_xml += (
                    "\n        <drmd:materialIdentifier>\n"
                    f"          <drmd:scheme>{escape_xml(identifier.get('scheme') or 'MaterialID')}</drmd:scheme>\n"
                    f"          <drmd:value>{escape_xml(identifier.get('value', ''))}</drmd:value>\n"
                    "        </drmd:materialIdentifier>"
                )
            materials_xml += "\n      </drmd:materialIdentifiers>"

        min_sample = material.get("minimumSampleSize", "")
        materials_xml += (
            "\n      <drmd:minimumSampleSize>\n"
            f"        <dcc:itemQuantity>{_render_primitive_quantity(str(min_sample))}\n"
            "        </dcc:itemQuantity>\n"
            "      </drmd:minimumSampleSize>"
        )

        item_quant = material.get("itemQuantities", "")
        if item_quant:
            materials_xml += (
                "\n      <drmd:itemQuantities>\n"
                f"        <dcc:itemQuantity>{_render_primitive_quantity(str(item_quant))}\n"
                "        </dcc:itemQuantity>\n"
                "      </drmd:itemQuantities>"
            )

        materials_xml += "\n    </drmd:material>"
    materials_xml += "\n  </drmd:materials>"

    properties_xml = "\n  <drmd:materialPropertiesList>"
    for prop in properties:
        is_cert = str(bool(prop.get("isCertified", False))).lower()
        properties_xml += (
            f"\n    <drmd:materialProperties isCertified=\"{is_cert}\">\n"
            "      <drmd:name>\n"
            f"        <dcc:content>{escape_xml(prop.get('name', ''))}</dcc:content>\n"
            "      </drmd:name>"
        )

        if prop.get("description"):
            properties_xml += (
                "\n      <drmd:description>\n"
                f"        <dcc:content>{escape_xml(prop.get('description', ''))}</dcc:content>\n"
                "      </drmd:description>"
            )

        if prop.get("procedures"):
            properties_xml += (
                "\n      <drmd:procedures>\n"
                "        <dcc:usedMethod>\n"
                "          <dcc:name>\n"
                "            <dcc:content>Procedure</dcc:content>\n"
                "          </dcc:name>\n"
                "          <dcc:description>\n"
                f"            <dcc:content>{escape_xml(prop.get('procedures', ''))}</dcc:content>\n"
                "          </dcc:description>\n"
                "        </dcc:usedMethod>\n"
                "      </drmd:procedures>"
            )

        properties_xml += "\n      <drmd:results>"
        for result in prop.get("results", []):
            properties_xml += (
                "\n        <drmd:result>\n"
                "          <drmd:name>\n"
                f"            <dcc:content>{escape_xml(result.get('name') or 'Values')}</dcc:content>\n"
                "          </drmd:name>"
            )

            if result.get("description"):
                properties_xml += (
                    "\n          <drmd:description>\n"
                    f"            <dcc:content>{escape_xml(result.get('description', ''))}</dcc:content>\n"
                    "          </drmd:description>"
                )

            properties_xml += "\n          <drmd:data>\n            <drmd:list>"
            for quantity in result.get("quantities", []):
                raw_value = quantity.get("dsiValue") or quantity.get("value", "")
                raw_unit = quantity.get("dsiUnit") or quantity.get("unit", "")
                value, unit = convert_to_dsi(raw_value, raw_unit)
                cas_number = get_cas_number(quantity.get("name", ""))
                properties_xml += (
                    "\n              <drmd:quantity>\n"
                    "                <dcc:name>\n"
                    f"                  <dcc:content>{escape_xml(quantity.get('name', ''))}</dcc:content>\n"
                    "                </dcc:name>\n"
                    "                <si:real>\n"
                    f"                  <si:value>{escape_xml(value)}</si:value>\n"
                    f"                  <si:unit>{escape_xml(unit)}</si:unit>"
                )

                if quantity.get("uncertainty"):
                    properties_xml += (
                        "\n                  <si:measurementUncertaintyUnivariate>\n"
                        "                    <si:expandedMU>\n"
                        f"                      <si:valueExpandedMU>{escape_xml(quantity.get('uncertainty', ''))}</si:valueExpandedMU>"
                    )
                    if quantity.get("coverageFactor"):
                        properties_xml += (
                            f"\n                      <si:coverageFactor>{escape_xml(quantity.get('coverageFactor', ''))}</si:coverageFactor>"
                        )
                    if quantity.get("coverageProbability"):
                        properties_xml += (
                            f"\n                      <si:coverageProbability>{escape_xml(quantity.get('coverageProbability', ''))}</si:coverageProbability>"
                        )
                    properties_xml += (
                        "\n                    </si:expandedMU>\n"
                        "                  </si:measurementUncertaintyUnivariate>"
                    )

                properties_xml += "\n                </si:real>"

                if cas_number:
                    properties_xml += (
                        "\n                <drmd:propertyIdentifiers>\n"
                        "                  <drmd:propertyIdentifier>\n"
                        "                    <drmd:scheme>CAS</drmd:scheme>\n"
                        f"                    <drmd:value>{escape_xml(cas_number)}</drmd:value>\n"
                        f"                    <drmd:link>https://commonchemistry.cas.org/detail?cas_rn={escape_xml(cas_number)}</drmd:link>\n"
                        "                  </drmd:propertyIdentifier>\n"
                        "                </drmd:propertyIdentifiers>"
                    )

                properties_xml += "\n              </drmd:quantity>"

            properties_xml += "\n            </drmd:list>\n          </drmd:data>\n        </drmd:result>"

        properties_xml += "\n      </drmd:results>\n    </drmd:materialProperties>"

    properties_xml += "\n  </drmd:materialPropertiesList>"

    statements_xml = "\n  <drmd:statements>"

    def add_statement(tag: str, name: str, content: str) -> str:
        if not content:
            return ""
        return (
            f"\n    <drmd:{tag}>\n"
            "      <dcc:name>\n"
            f"        <dcc:content>{escape_xml(name)}</dcc:content>\n"
            "      </dcc:name>\n"
            f"      <dcc:content>{escape_xml(content)}</dcc:content>\n"
            f"    </drmd:{tag}>"
        )

    statements_xml += add_statement("intendedUse", "Intended Use", statements.get("intendedUse", ""))
    statements_xml += add_statement(
        "storageInformation", "Storage Information", statements.get("storageInformation", "")
    )
    statements_xml += add_statement(
        "instructionsForHandlingAndUse", "Handling Instructions", statements.get("handlingInstructions", "")
    )
    statements_xml += add_statement(
        "metrologicalTraceability", "Metrological Traceability", statements.get("metrologicalTraceability", "")
    )
    statements_xml += add_statement("subcontractors", "Subcontractors", statements.get("subcontractors", ""))
    statements_xml += add_statement(
        "referenceToCertificationReport",
        "Reference to Certification Report",
        statements.get("referenceToCertificationReport", ""),
    )
    statements_xml += add_statement(
        "healthAndSafetyInformation", "Health And Safety Information", statements.get("healthAndSafety", "")
    )
    statements_xml += add_statement("legalNotice", "Legal Notice", statements.get("legalNotice", ""))
    statements_xml += "\n  </drmd:statements>"

    extra_xml = ""
    if data.get("generalComment"):
        extra_xml += f"\n  <drmd:comment>{escape_xml(data.get('generalComment'))}</drmd:comment>"
    for document in data.get("binaryDocuments", []):
        if document.get("data"):
            extra_xml += f"\n  <drmd:document>{document['data']}</drmd:document>"

    footer = "\n</drmd:digitalReferenceMaterialDocument>"
    return header + admin_xml + materials_xml + properties_xml + statements_xml + extra_xml + footer
