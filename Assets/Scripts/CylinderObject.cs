﻿using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public class CylinderObject : WorldObject
{
    public float y_scale;
    static MaterialCache mcache;
    static MaterialCache mcache_highlight;

    public override void UpdateWorldObject(WorldScript ws, float[] data)
    {
        if (mcache == null)
            mcache = new MaterialCache(GetComponentInChildren<MeshRenderer>().sharedMaterial);

        Vector3 p1 = GetVec3(data, 0);
        Vector3 p2 = GetVec3(data, 3);

        Vector3 scale = transform.localScale;
        scale.y = Vector3.Distance(p1, p2) * y_scale + 0.0025f;
        transform.localScale = scale;
        transform.localPosition = (p1 + p2) * 0.5f;
        if (p1 != p2)
            transform.localRotation = Quaternion.LookRotation(p2 - p1) * Quaternion.LookRotation(Vector3.up);

        Color col = data.Length > 6 ? GetColor24(data, 6) : Color.clear;   /* Color.clear == use default */
        Color col2 = data.Length > 7 ? GetColor24(data, 7) : col;
        foreach (var rend in GetComponentsInChildren<MeshRenderer>())
        {
            rend.sharedMaterial = mcache.Get(col);
            Color swap = col; col = col2; col2 = swap;
        }
        if (kind == WorldScript.Kind.SelectedStem)
        {
            var rend = GetComponentInChildren<MeshRenderer>();
            var mats = rend.sharedMaterials;

            if (mcache_highlight == null)
                mcache_highlight = new MaterialCache(mats[1],
                    MaterialCache.BuildHighlightMaterial);

            mats[1] = mcache_highlight.Get(col);
            rend.sharedMaterials = mats;
        }
    }
}
