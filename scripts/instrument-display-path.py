#!/usr/bin/env python3
"""Add opt-in-by-default PanVK Android display-path diagnostics for MC7 tests."""
from pathlib import Path

def replace_once(path, old, new):
    p = Path(path)
    s = p.read_text()
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{path}: expected one anchor, found {n}: {old[:100]!r}")
    p.write_text(s.replace(old, new, 1))

queue = "src/panfrost/vulkan/csf/panvk_vX_gpu_queue.c"
replace_once(queue,
"""   if (vk_queue_is_lost(vk_queue))
      return VK_ERROR_DEVICE_LOST;
""",
"""   if (vk_queue_is_lost(vk_queue)) {
      mesa_logi("[panvk-display] queue_submit rejected: queue already lost queue=%p", vk_queue);
      return VK_ERROR_DEVICE_LOST;
   }

   mesa_logi("[panvk-display] queue_submit begin queue=%p submit=%p", vk_queue, vk_submit);
""")
replace_once(queue,
"""      result = panvk_queue_submit_ioctl_kbase(&submit, vk_submit);
      if (result != VK_SUCCESS)
         goto out;
""",
"""      result = panvk_queue_submit_ioctl_kbase(&submit, vk_submit);
      mesa_logi("[panvk-display] queue_submit kbase ioctl result=%d queue=%p", result, vk_queue);
      if (result != VK_SUCCESS)
         goto out;
""")
replace_once(queue,
"""   result = panvk_queue_submit_ioctl(&submit);
   if (result != VK_SUCCESS)
      goto out;
""",
"""   result = panvk_queue_submit_ioctl(&submit);
   mesa_logi("[panvk-display] queue_submit panthor ioctl result=%d queue=%p", result, vk_queue);
   if (result != VK_SUCCESS)
      goto out;
""")
replace_once(queue,
"""out:
   panvk_queue_submit_cleanup_storage(&submit, &stack_storage);
""",
"""out:
   mesa_logi("[panvk-display] queue_submit end result=%d queue=%p", result, vk_queue);
   panvk_queue_submit_cleanup_storage(&submit, &stack_storage);
""")

android = "src/panfrost/vulkan/panvk_android.c"
replace_once(android,
"""   result = vk_android_get_anb_layout(create_info, &mod_info, layouts,
                                      PANVK_MAX_PLANES);
   if (result != VK_SUCCESS)
      return result;
""",
"""   result = vk_android_get_anb_layout(create_info, &mod_info, layouts,
                                      PANVK_MAX_PLANES);
   mesa_logi("[panvk-display] ANB layout result=%d format=%u extent=%ux%u hal=%d stride=%d",
             result, create_info->format, create_info->extent.width,
             create_info->extent.height,
             ((const VkNativeBufferANDROID *)vk_find_struct_const(create_info->pNext, NATIVE_BUFFER_ANDROID))->format,
             ((const VkNativeBufferANDROID *)vk_find_struct_const(create_info->pNext, NATIVE_BUFFER_ANDROID))->stride);
   if (result == VK_SUCCESS)
      mesa_logi("[panvk-display] ANB layout accepted modifier=0x%llx planes=%u pitch0=%llu size0=%llu",
                (unsigned long long)mod_info.drmFormatModifier,
                mod_info.drmFormatModifierPlaneCount,
                (unsigned long long)layouts[0].rowPitch,
                (unsigned long long)layouts[0].size);
   if (result != VK_SUCCESS)
      return result;
""")
replace_once(android,
"""   result =
      vk_android_import_anb_memory(&dev->vk, &img->vk, anb, &dev->vk.alloc);
   if (result != VK_SUCCESS)
      return result;

   *out_mem_handle = img->vk.anb_memory;
""",
"""   result =
      vk_android_import_anb_memory(&dev->vk, &img->vk, anb, &dev->vk.alloc);
   mesa_logi("[panvk-display] ANB memory import result=%d image=%p", result, bind_info->image);
   if (result != VK_SUCCESS)
      return result;

   *out_mem_handle = img->vk.anb_memory;
   mesa_logi("[panvk-display] ANB WSI memory ready image=%p memory=%p", bind_info->image, *out_mem_handle);
""")

print("Added PanVK display diagnostics for ANB layout/import and Kbase queue submissions.")
